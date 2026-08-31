"""
WHY: Node 3b — external claim verification. This node is the "trust but verify"
layer of SCREEN. The extract_evidence node classifies claims by internal
consistency; this node goes external and tests the highest-stakes claims
against GitHub, web search, and portfolio URLs.

A Tier B claim is a candidate's word. A Tier A claim is a candidate's word
confirmed by a third party. This node does that upgrade where possible.

HOW:
1. Scan all claims for verifiable signals (GitHub repos, company names, portfolios)
2. Call GitHub API for repo/star verification (unauthenticated: 60 req/hr)
3. Call Tavily web search for company/achievement verification (if API key set)
4. Fetch portfolio URL from CV text if present
5. Reconstruct EvidenceBundle with updated claims and any new contradictions
"""

import re
import time
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from screen.core.config import settings
from screen.core.exceptions import StateTransitionError
from screen.core.logging_config import get_logger
from screen.core.trajectory import make_trajectory_entry
from screen.schemas.evidence import (
    SIGNAL_WEIGHTS,
    Claim,
    Contradiction,
    EvidenceBundle,
    VerificationResult,
    VerificationSource,
)
from screen.schemas.state import ScreeningState

logger = get_logger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
_GITHUB_USER_REPOS_URL = "https://api.github.com/users/{username}/repos"
_GITHUB_URL_RE = re.compile(r"github\.com/([a-zA-Z0-9_-]+)(?:/([a-zA-Z0-9_.-]+))?")
_PORTFOLIO_URL_RE = re.compile(
    r"https?://(?!(?:www\.)?github\.com)(?!(?:www\.)?linkedin\.com)"
    r"[a-zA-Z0-9._-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?"
)
_GITHUB_CLAIM_KEYWORDS = re.compile(
    r"\bgithub\b|\brepo(?:sitory)?\b|\bstar[s]?\b|\bopen.?source\b|\bfork[s]?\b",
    re.IGNORECASE,
)
_COMPANY_CLAIM_KEYWORDS = re.compile(
    r"\bfounded\b|\bincorporated\b|\blaunched\b|\bstarted\b|\bcreated\b|\bestablished\b",
    re.IGNORECASE,
)
# WHY: Portfolio URL denylist prevents fetching CDN, font, and analytics URLs
# that leak into CV text from PDF conversion or HTML-formatted CVs.
_PORTFOLIO_URL_DENYLIST = re.compile(
    r"(?:googleapis|cloudflare|amazonaws|fonts\.|cdn\.|ajax\.|tracking\.|analytics\.)",
    re.IGNORECASE,
)


# ── GitHub helpers ─────────────────────────────────────────────────────────────

def _build_github_headers() -> dict[str, str]:
    """
    WHY: GitHub allows 60 unauthenticated requests/hour. With a token we get
    5,000/hour. We use the token if configured, fall back to unauthenticated.

    HOW: getattr pattern because settings.github_token won't exist until
    config.py is updated — safe degradation path.

    Returns:
        Dict of HTTP headers for GitHub API requests.
    """
    headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError)),
)
def _fetch_github_repos(username: str) -> list[dict[str, Any]]:
    """
    WHY: Fetches the top 5 repos by star count for a GitHub user. Used both to
    verify repo claims in the CV and to discover unclaimed repos.

    HOW: Sorted by stars descending, limited to 5. Returns empty list on any
    error so the caller can degrade gracefully without crashing the pipeline.

    Args:
        username: GitHub username extracted from CV text or claim.

    Returns:
        List of repo dicts from GitHub API (may be empty on failure).
    """
    url = _GITHUB_USER_REPOS_URL.format(username=username)
    with httpx.Client(timeout=10) as client:
        response = client.get(
            url,
            params={"sort": "stars", "direction": "desc", "per_page": 5},
            headers=_build_github_headers(),
        )
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError)),
)
def _fetch_portfolio_text(url: str) -> str:
    """
    WHY: A portfolio URL in the CV is a direct link to verifiable evidence.
    Fetching it lets us confirm the site is live and surface skill signals.

    HOW: Returns the raw text content, truncated to 2000 chars to avoid
    excessive memory use. Returns empty string on failure.

    Args:
        url: Portfolio URL to fetch.

    Returns:
        Page text content (truncated) or empty string on failure.
    """
    with httpx.Client(timeout=10, follow_redirects=True) as client:
        response = client.get(url, headers={"User-Agent": "SCREEN-Agent/1.0"})
        response.raise_for_status()
        return response.text[:2000]


# ── Tavily helper ──────────────────────────────────────────────────────────────

def _tavily_search(query: str, max_results: int = 3) -> list[dict[str, Any]]:
    """
    WHY: Tavily is used for web verification of company existence/founding dates
    and achievement claims. Degrades gracefully to empty list if API key is
    not configured — no crash, just no web verification.

    HOW: Returns Tavily result dicts with 'title', 'url', 'content', 'score'.
    Caller inspects content to decide if the claim is confirmed or contradicted.

    Args:
        query: Search query string.
        max_results: Maximum results to return.

    Returns:
        List of result dicts, or empty list if Tavily unavailable.
    """
    if not settings.tavily_api_key:
        logger.debug("Tavily API key not configured — skipping web search", query=query)
        return []

    try:
        from tavily import TavilyClient  # noqa: PLC0415

        client = TavilyClient(api_key=settings.tavily_api_key)
        result = client.search(query, max_results=max_results)
        return result.get("results", [])  # type: ignore[no-any-return]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Tavily search failed", query=query, error=str(exc))
        return []


# ── Claim verification logic ───────────────────────────────────────────────────

def _verify_claim_via_github(
    claim: Claim,
    username: str,
    repos: list[dict[str, Any]],
) -> Claim:
    """
    WHY: Upgrades a Tier B GitHub claim to Tier A if the GitHub API confirms
    a repo exists with meaningful star count. Attaches VerificationResult so
    the audit trail shows exactly what was checked and what was found.

    HOW: Tries to match a repo name mentioned in the claim text. Falls back to
    the most-starred repo if no name match. Never auto-downgrade — just records
    what was found and upgrades if the repo exists.

    Args:
        claim: The original Claim to verify.
        username: GitHub username found in CV.
        repos: List of repo dicts from GitHub API.

    Returns:
        Updated Claim with verification attached (tier upgraded to A if confirmed).
    """
    if not repos:
        verification = VerificationResult(
            source=VerificationSource.GITHUB_API,
            query_used=f"github.com/{username}",
            found=False,
            summary=f"GitHub user '{username}' found but no public repos returned.",
            url=f"https://github.com/{username}",
            tier_change=None,
        )
        return Claim(
            text=claim.text,
            tier=claim.tier,
            confidence_weight=claim.confidence_weight,
            source_location=claim.source_location,
            is_verifiable_externally=claim.is_verifiable_externally,
            verification=verification,
        )

    # Try to match a repo mentioned in the claim text
    matched_repo: dict[str, Any] | None = None
    for repo in repos:
        repo_name: str = repo.get("name", "").lower()
        if repo_name and repo_name in claim.text.lower():
            matched_repo = repo
            break

    # Fall back to most-starred repo if no name match
    if matched_repo is None:
        matched_repo = repos[0]

    repo_name = matched_repo.get("name", "unknown")
    repo_stars: int = matched_repo.get("stargazers_count", 0)
    repo_url: str = matched_repo.get("html_url", f"https://github.com/{username}/{repo_name}")

    verification = VerificationResult(
        source=VerificationSource.GITHUB_API,
        query_used=f"github.com/{username}",
        found=True,
        summary=(
            f"GitHub repo '{repo_name}' confirmed with {repo_stars} stars. "
            f"Claim externally verifiable via public GitHub profile."
        ),
        url=repo_url,
        tier_change="B->A" if claim.tier == "B" else None,
    )

    new_tier = "A" if claim.tier == "B" else claim.tier
    return Claim(
        text=claim.text,
        tier=new_tier,
        confidence_weight=SIGNAL_WEIGHTS[new_tier],
        source_location=claim.source_location,
        is_verifiable_externally=True,
        verification=verification,
    )


def _detect_temporal_contradiction(claim_text: str, web_content: str) -> bool:
    """
    WHY: Fast deterministic check for the most common external contradiction:
    a company founded after the candidate claims to have worked there.

    HOW: Extracts founding year from web content using keyword regex, then
    compares to the earliest year mentioned in the claim. Returns True only
    when confident of a conflict — false negatives are acceptable, false
    positives send candidates to unnecessary human review.

    Args:
        claim_text: The claim being verified.
        web_content: Text content from the web search result.

    Returns:
        True if a likely temporal contradiction is detected.
    """
    claim_years = [int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", claim_text)]
    if not claim_years:
        return False

    founding_match = re.search(
        r"(?:founded|incorporated|established|launched)\s+(?:in\s+)?(\d{4})",
        web_content,
        re.IGNORECASE,
    )
    if not founding_match:
        return False

    founding_year = int(founding_match.group(1))
    earliest_claim_year = min(claim_years)
    return earliest_claim_year < founding_year


def _build_safe_search_query(claim: Claim) -> str:
    """
    WHY: External search APIs must never receive PII. claim.text is paraphrased
    but may still contain names (e.g., "reported to Jane Okello"). We build the
    query from source_location instead — a structured pointer ("Role at DataCorp
    2019–2022, bullet 3") that contains only company name and dates, never people.

    HOW: Extracts company name and year from source_location using regex. Falls
    back to the first 60 chars of source_location if parsing fails. Never uses
    claim.text for external queries.

    Args:
        claim: Claim to build a safe search query for.

    Returns:
        Search query string safe for external API submission.
    """
    source = claim.source_location

    # Extract company from "Role at COMPANY DATES, bullet N" pattern
    company_match = re.search(r"\bat\s+([^,\d\n]+?)(?:\s+\d{4}|,|\n|$)", source)
    company = company_match.group(1).strip() if company_match else ""

    # Extract year from source_location
    year_match = re.search(r"\b(19|20)\d{2}\b", source)
    year = year_match.group(0) if year_match else ""

    if company and year:
        suffix = "founded date" if _COMPANY_CLAIM_KEYWORDS.search(claim.text) else "verify"
        return f"{company} {year} {suffix}"
    if company:
        return f"{company} company verify"

    # Final fallback: use source_location pointer only (still safe — no claim.text)
    return f"{source[:60]} verify"


def _verify_claim_via_web(claim: Claim) -> tuple[Claim, Contradiction | None]:
    """
    WHY: Uses Tavily to check company existence and achievement claims. If search
    returns contradicting evidence, a Contradiction is added to the bundle and
    the case is routed to human review.

    HOW: Builds a PII-safe search query from source_location (not claim.text).
    Applies _detect_temporal_contradiction heuristic on the top result.

    Args:
        claim: The Tier B claim to verify via web search.

    Returns:
        Tuple of (updated_claim, contradiction_or_None).
    """
    query = _build_safe_search_query(claim)
    results = _tavily_search(query)

    if not results:
        verification = VerificationResult(
            source=VerificationSource.WEB_SEARCH,
            query_used=query,
            found=False,
            summary="Web search returned no results. Claim remains at current tier.",
            tier_change=None,
        )
        updated_claim = Claim(
            text=claim.text,
            tier=claim.tier,
            confidence_weight=claim.confidence_weight,
            source_location=claim.source_location,
            is_verifiable_externally=claim.is_verifiable_externally,
            verification=verification,
        )
        return updated_claim, None

    top_result = results[0]
    result_content: str = top_result.get("content", "")
    result_url: str = top_result.get("url", "")

    contradiction: Contradiction | None = None
    contradiction_detected = _detect_temporal_contradiction(claim.text, result_content)

    if contradiction_detected:
        contradiction = Contradiction(
            claim_a=claim.text,
            claim_b=f"Web source indicates: {result_content[:200]}",
            contradiction_type="temporal",
            severity="moderate",
            explanation=(
                f"External source ({result_url}) suggests a timing conflict "
                f"with the candidate's stated dates."
            ),
        )
        verification = VerificationResult(
            source=VerificationSource.WEB_SEARCH,
            query_used=query,
            found=True,
            summary=(
                f"Web search found potential temporal contradiction. "
                f"Source: {result_url}. Human review recommended."
            ),
            url=result_url,
            tier_change=None,
        )
        updated_claim = Claim(
            text=claim.text,
            tier=claim.tier,
            confidence_weight=claim.confidence_weight,
            source_location=claim.source_location,
            is_verifiable_externally=True,
            verification=verification,
        )
    else:
        verification = VerificationResult(
            source=VerificationSource.WEB_SEARCH,
            query_used=query,
            found=True,
            summary=(
                f"Web search found supporting context. No contradictions detected. "
                f"Source: {result_url}"
            ),
            url=result_url,
            tier_change="B->A" if claim.tier == "B" else None,
        )
        new_tier = "A" if claim.tier == "B" else claim.tier
        updated_claim = Claim(
            text=claim.text,
            tier=new_tier,
            confidence_weight=SIGNAL_WEIGHTS[new_tier],
            source_location=claim.source_location,
            is_verifiable_externally=True,
            verification=verification,
        )

    return updated_claim, contradiction


# ── Portfolio verification ─────────────────────────────────────────────────────

def _extract_github_username(cv_text: str) -> str | None:
    """
    WHY: GitHub usernames in CVs are almost always the candidate's own profile.
    Extracting the username lets us verify existing claims and discover repos.

    HOW: Regex matches github.com/{username}. Excludes known GitHub sub-paths.

    Args:
        cv_text: Raw CV text.

    Returns:
        GitHub username string, or None if not found.
    """
    match = _GITHUB_URL_RE.search(cv_text)
    if not match:
        return None
    username = match.group(1)
    if username.lower() in {"orgs", "organizations", "features", "enterprise", "topics"}:
        return None
    return username


def _verify_portfolio(cv_text: str) -> Claim | None:
    """
    WHY: A live portfolio URL is a Tier A signal — the candidate is publicly
    demonstrating their work. We add this as a new claim rather than modifying
    an existing one. Returns None on any failure (no crash).

    HOW: Extracts first non-social, non-CDN URL from CV text, fetches it,
    confirms it returns meaningful content, adds a Tier A claim with
    VerificationResult. Denylist prevents fetching CDN/font/analytics URLs
    that may appear in PDF-converted or HTML-formatted CVs.

    Args:
        cv_text: Raw CV text to extract portfolio URL from.

    Returns:
        New Tier A Claim if portfolio is live, else None.
    """
    match = _PORTFOLIO_URL_RE.search(cv_text)
    if not match:
        return None
    portfolio_url = match.group(0)

    # Reject known CDN, font, and analytics URLs — not personal portfolio sites
    if _PORTFOLIO_URL_DENYLIST.search(portfolio_url):
        logger.debug("Portfolio URL rejected by denylist", url=portfolio_url)
        return None

    try:
        content = _fetch_portfolio_text(portfolio_url)
    except Exception as exc:  # noqa: BLE001
        logger.info("Portfolio URL fetch failed", url=portfolio_url, error=str(exc))
        return None

    if not content or len(content.strip()) < 100:
        return None

    verification = VerificationResult(
        source=VerificationSource.PORTFOLIO_FETCH,
        query_used=portfolio_url,
        found=True,
        summary=(
            "Portfolio URL is live and returned content. "
            "Candidate has a publicly accessible portfolio."
        ),
        url=portfolio_url,
        tier_change=None,
    )
    return Claim(
        text=f"Candidate maintains a live public portfolio at {portfolio_url}",
        tier="A",
        confidence_weight=SIGNAL_WEIGHTS["A"],
        source_location="CV text — portfolio URL",
        is_verifiable_externally=True,
        verification=verification,
    )


def _build_new_claims_from_repos(
    username: str,
    repos: list[dict[str, Any]],
    existing_claims: list[Claim],
) -> list[Claim]:
    """
    WHY: If GitHub API reveals repos with stars that the candidate didn't mention,
    those are legitimate Tier A signals. The cap at settings.max_new_claims_from_github
    prevents the bundle from being dominated by auto-generated claims.

    HOW: Skips repos with 0 stars and repos already referenced in existing claims.
    Creates a Tier A claim for each remaining repo up to the cap.

    Args:
        username: GitHub username.
        repos: Top repos from GitHub API.
        existing_claims: Existing claims to check for duplicates.

    Returns:
        List of new Tier A claims (at most settings.max_new_claims_from_github).
    """
    existing_texts = " ".join(c.text.lower() for c in existing_claims)
    new_claims: list[Claim] = []

    for repo in repos:
        if len(new_claims) >= settings.max_new_claims_from_github:
            break

        repo_name: str = repo.get("name", "")
        repo_stars: int = repo.get("stargazers_count", 0)
        repo_url: str = repo.get("html_url", f"https://github.com/{username}/{repo_name}")
        repo_desc: str = repo.get("description", "") or ""

        if repo_stars < 1:
            continue
        if repo_name.lower() in existing_texts:
            continue

        verification = VerificationResult(
            source=VerificationSource.GITHUB_API,
            query_used=f"github.com/{username}",
            found=True,
            summary=(
                f"GitHub repo '{repo_name}' discovered via API: "
                f"{repo_stars} stars. Not mentioned in CV."
            ),
            url=repo_url,
            tier_change=None,
        )
        desc_fragment = f" — {repo_desc[:80]}" if repo_desc else ""
        new_claims.append(
            Claim(
                text=f"Public GitHub repo '{repo_name}' with {repo_stars} stars{desc_fragment}",
                tier="A",
                confidence_weight=SIGNAL_WEIGHTS["A"],
                source_location=f"GitHub API discovery — github.com/{username}/{repo_name}",
                is_verifiable_externally=True,
                verification=verification,
            )
        )

    return new_claims


# ── Main node ──────────────────────────────────────────────────────────────────

def verify_claims_node(state: ScreeningState) -> dict[str, Any]:
    """
    WHY: Sits between extract_evidence and analyze_fit. Takes the LLM-classified
    EvidenceBundle and runs external tool calls to upgrade verified claims from
    Tier B->A, surface contradictions from external sources, and discover
    unclaimed public evidence (GitHub repos, live portfolio).

    HOW:
    1. Validate state prerequisites (evidence_bundle, screening_input)
    2. Extract GitHub username from CV text; fetch repos via GitHub API
    3. For each Tier B claim with GitHub keywords -> verify via GitHub API
    4. For each Tier B claim marked is_verifiable_externally -> verify via Tavily
    5. Fetch and validate portfolio URL from CV text if present
    6. Discover unclaimed GitHub repos not mentioned in CV
    7. Reconstruct EvidenceBundle (frozen model — full reconstruction required)
    8. Build trajectory entry summarising upgrades and new contradictions

    Args:
        state: Current LangGraph ScreeningState.

    Returns:
        dict with keys: evidence_bundle, trajectory, total_cost_usd.

    Raises:
        StateTransitionError: If evidence_bundle or screening_input are missing.
    """
    node_name = "verify_claims"
    start_ms = time.time() * 1000

    evidence_bundle: EvidenceBundle | None = state.get("evidence_bundle")
    if evidence_bundle is None:
        raise StateTransitionError(node_name, "evidence_bundle")

    screening_input = state.get("screening_input")
    if screening_input is None:
        raise StateTransitionError(node_name, "screening_input")

    candidate_id = screening_input.candidate_id
    cv_text: str = screening_input.cv_text

    logger.info(
        "verify_claims started",
        node=node_name,
        candidate_id=candidate_id,
        num_claims=len(evidence_bundle.claims),
    )

    # ── Working state accumulators ─────────────────────────────────────────────
    updated_claims: list[Claim] = []
    new_contradictions: list[Contradiction] = list(evidence_bundle.contradictions)
    upgrades_count: int = 0
    verifications_attempted: int = 0
    new_contradictions_count: int = 0

    # ── Step 1: GitHub — fetch repos once for the whole run ───────────────────
    github_username: str | None = _extract_github_username(cv_text)
    github_repos: list[dict[str, Any]] = []

    if github_username:
        try:
            github_repos = _fetch_github_repos(github_username)
            logger.info(
                "GitHub repos fetched",
                node=node_name,
                candidate_id=candidate_id,
                username=github_username,
                repo_count=len(github_repos),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "GitHub API call failed — skipping GitHub verification",
                node=node_name,
                candidate_id=candidate_id,
                username=github_username,
                error=str(exc),
            )

    # ── Step 2: Process each existing claim ───────────────────────────────────
    for claim in evidence_bundle.claims:
        # Only attempt verification on Tier B claims.
        # Tier A: already verified. Tier C: too vague. Tier D: already contradicted.
        if claim.tier != "B":
            updated_claims.append(claim)
            continue

        # Route to GitHub verification if claim text references GitHub
        if github_username and github_repos and _GITHUB_CLAIM_KEYWORDS.search(claim.text):
            verifications_attempted += 1
            try:
                updated = _verify_claim_via_github(claim, github_username, github_repos)
                if updated.tier != claim.tier:
                    upgrades_count += 1
                updated_claims.append(updated)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "GitHub claim verification failed — keeping original",
                    node=node_name,
                    candidate_id=candidate_id,
                    claim_snippet=claim.text[:60],
                    error=str(exc),
                )
                updated_claims.append(claim)
            continue

        # Route to web search if claim is externally verifiable or has company keywords
        if claim.is_verifiable_externally or _COMPANY_CLAIM_KEYWORDS.search(claim.text):
            verifications_attempted += 1
            try:
                updated, contradiction = _verify_claim_via_web(claim)
                if updated.tier != claim.tier:
                    upgrades_count += 1
                updated_claims.append(updated)
                if contradiction is not None:
                    new_contradictions.append(contradiction)
                    new_contradictions_count += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Web claim verification failed — keeping original",
                    node=node_name,
                    candidate_id=candidate_id,
                    claim_snippet=claim.text[:60],
                    error=str(exc),
                )
                updated_claims.append(claim)
            continue

        # Tier B claim with no verification route — keep as is
        updated_claims.append(claim)

    # ── Step 3: Portfolio URL verification ────────────────────────────────────
    portfolio_claim: Claim | None = None
    try:
        portfolio_claim = _verify_portfolio(cv_text)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Portfolio verification failed — skipping",
            node=node_name,
            candidate_id=candidate_id,
            error=str(exc),
        )

    if portfolio_claim is not None:
        updated_claims.append(portfolio_claim)
        logger.info(
            "Portfolio claim added",
            node=node_name,
            candidate_id=candidate_id,
            url=portfolio_claim.verification.url if portfolio_claim.verification else None,
        )

    # ── Step 4: GitHub repo discovery (unclaimed repos) ───────────────────────
    if github_username and github_repos:
        try:
            new_repo_claims = _build_new_claims_from_repos(
                github_username, github_repos, updated_claims
            )
            updated_claims.extend(new_repo_claims)
            if new_repo_claims:
                logger.info(
                    "New repo claims added from GitHub discovery",
                    node=node_name,
                    candidate_id=candidate_id,
                    count=len(new_repo_claims),
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "GitHub repo discovery failed — skipping",
                node=node_name,
                candidate_id=candidate_id,
                error=str(exc),
            )

    # ── Step 5: Reconstruct EvidenceBundle ────────────────────────────────────
    # WHY: EvidenceBundle uses ConfigDict(frozen=True). We can't mutate it —
    # we must construct a fresh instance with updated claims and contradictions.
    new_has_critical = any(c.severity == "critical" for c in new_contradictions)

    # WHY: Re-evaluate has_unverifiable_high_stakes_claim after verification runs.
    # Claims that were Tier B + externally verifiable + unverified may now have a
    # VerificationResult. If all such claims have been resolved, the flag can clear.
    # We only clear it if the original bundle set it AND no B/C external claims
    # remain without a verification attempt — preserving conservative escalation.
    still_unverified_external = any(
        c.tier in ("B", "C") and c.is_verifiable_externally and c.verification is None
        for c in updated_claims
    )
    new_has_unverifiable = (
        evidence_bundle.has_unverifiable_high_stakes_claim and still_unverified_external
    )

    updated_bundle = EvidenceBundle(
        candidate_id=evidence_bundle.candidate_id,
        claims=updated_claims,
        contradictions=new_contradictions,
        silence_flags=evidence_bundle.silence_flags,
        builder_signals=evidence_bundle.builder_signals,
        maintainer_signals=evidence_bundle.maintainer_signals,
        builder_maintainer_verdict=evidence_bundle.builder_maintainer_verdict,
        has_critical_contradiction=new_has_critical,
        has_unverifiable_high_stakes_claim=new_has_unverifiable,
    )

    # ── Step 6: Trajectory entry ──────────────────────────────────────────────
    # WHY: GitHub API is free; Tavily is cheap enough to treat as $0 per-run.
    # If Tavily cost becomes significant in production, add per-search cost tracking.
    cost_usd = 0.0

    tier_a_after = sum(1 for c in updated_claims if c.tier == "A")
    tier_b_after = sum(1 for c in updated_claims if c.tier == "B")

    trajectory_entry = make_trajectory_entry(
        node=node_name,
        start_time_ms=start_ms,
        reasoning_summary=(
            f"Verified {verifications_attempted} claim(s) using external tools. "
            f"{upgrades_count} claim(s) upgraded to Tier A. "
            f"{new_contradictions_count} new external contradiction(s) found. "
            f"GitHub: {'found user ' + github_username if github_username else 'not found'}. "
            f"Portfolio: {'verified' if portfolio_claim else 'not found'}. "
            f"Final bundle: {tier_a_after} Tier A, {tier_b_after} Tier B claims."
        ),
        output_summary=(
            f"{verifications_attempted} verified | {upgrades_count} upgraded | "
            f"{new_contradictions_count} new contradictions | "
            f"{len(updated_claims)} total claims"
        ),
        evidence_keys=[
            f"claim:{i}:verified"
            for i, c in enumerate(updated_claims)
            if c.verification is not None
        ][:20],
        model_used=None,
        cost_usd=cost_usd,
    )

    logger.info(
        "verify_claims complete",
        node=node_name,
        candidate_id=candidate_id,
        verifications_attempted=verifications_attempted,
        upgrades_count=upgrades_count,
        new_contradictions=new_contradictions_count,
        total_claims=len(updated_claims),
        duration_ms=trajectory_entry.duration_ms,
    )

    return {
        "evidence_bundle": updated_bundle,
        "trajectory": [trajectory_entry],
        "total_cost_usd": cost_usd,
    }
