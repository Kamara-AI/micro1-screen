"""
WHY: verify_claims is the external tool layer — GitHub API, Tavily web search,
and portfolio fetch. The core helper functions contain deterministic logic that
must be tested without live API calls. These tests cover:

  1. _detect_temporal_contradiction — catches founding-date inconsistencies
  2. _build_new_claims_from_repos — GitHub repo discovery, dedup, star cap
  3. _verify_claim_via_github — Tier B→A upgrade and graceful empty-repo path
  4. verify_claims_node — full node with external calls mocked out

Note: All tests use mocking for external calls. No API keys required.
"""

from unittest.mock import MagicMock, patch

import pytest

from screen.agent.nodes.verify_claims import (
    _build_new_claims_from_repos,
    _detect_temporal_contradiction,
    _verify_claim_via_github,
    verify_claims_node,
)
from screen.schemas.evidence import (
    SIGNAL_WEIGHTS,
    Claim,
    Contradiction,
    EvidenceBundle,
    VerificationSource,
)
from screen.schemas.input import ScreeningInput
from screen.schemas.state import initial_state


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_claim(
    text: str = "Worked at DataCorp from 2019",
    tier: str = "B",
    is_verifiable_externally: bool = False,
    source_location: str = "Role at DataCorp 2019-2022",
) -> Claim:
    return Claim(
        text=text,
        tier=tier,
        confidence_weight=SIGNAL_WEIGHTS[tier],
        source_location=source_location,
        is_verifiable_externally=is_verifiable_externally,
    )


def _make_bundle(claims: list[Claim] | None = None) -> EvidenceBundle:
    return EvidenceBundle(
        candidate_id="test_c01",
        claims=claims or [_make_claim()],
        contradictions=[],
        silence_flags=[],
        overall_signal_strength=0.7,
        has_critical_contradiction=False,
        has_unverifiable_high_stakes_claim=False,
    )


_DEFAULT_CV = (
    "Jane Smith — 7 years Python engineering. Built payment systems at Scale Corp. "
    "Led team of 8. Python, Go, PostgreSQL, Kafka. github.com/janesmith"
)
_DEFAULT_JD = (
    "Senior Backend Engineer. Requirements: 5+ years Python or Go, "
    "financial systems experience, team leadership. Series A fintech."
)


def _make_state(cv_text: str = _DEFAULT_CV) -> dict:
    inp = ScreeningInput(
        candidate_id="test_c01",
        role_seniority="senior",
        role_type="engineering",
        cv_text=cv_text,
        job_description=_DEFAULT_JD,
        hard_requirements=["5+ years Python"],
    )
    state = initial_state(inp)
    state["evidence_bundle"] = _make_bundle()
    return state


# ── _detect_temporal_contradiction ────────────────────────────────────────────

class TestDetectTemporalContradiction:
    """WHY: This is the key contradiction detector from Iteration 10. A false
    negative (missed contradiction) lets a fabricated CV through; a false
    positive sends a real candidate to unnecessary human review. Both errors
    are costly — we must validate the boundary conditions."""

    def test_detects_contradiction_when_claim_precedes_founding(self):
        """Claim year 2019 < founding year 2021 → should return True."""
        claim_text = "Head of Engineering at DataCorp from 2019"
        web_content = "DataCorp was founded in 2021 and grew to 50 employees."
        assert _detect_temporal_contradiction(claim_text, web_content) is True

    def test_no_contradiction_when_claim_after_founding(self):
        """Claim year 2022 > founding year 2019 → should return False."""
        claim_text = "Joined DataCorp as Tech Lead in 2022"
        web_content = "DataCorp was incorporated in 2019."
        assert _detect_temporal_contradiction(claim_text, web_content) is False

    def test_no_contradiction_when_claim_same_year_as_founding(self):
        """Claim year 2020 == founding year 2020 → no contradiction."""
        claim_text = "Co-founded DataCorp in 2020"
        web_content = "DataCorp was established in 2020."
        assert _detect_temporal_contradiction(claim_text, web_content) is False

    def test_returns_false_when_no_year_in_claim(self):
        """No year in claim → cannot determine conflict, return False."""
        claim_text = "Led engineering at DataCorp"
        web_content = "DataCorp was founded in 2020."
        assert _detect_temporal_contradiction(claim_text, web_content) is False

    def test_returns_false_when_no_founding_keyword_in_web_content(self):
        """Web content has no founding keyword → cannot determine year."""
        claim_text = "Worked at DataCorp from 2018"
        web_content = "DataCorp operates in East Africa and serves 10,000 users."
        assert _detect_temporal_contradiction(claim_text, web_content) is False

    def test_returns_false_when_web_content_empty(self):
        """Empty web content → no founding year found → False."""
        assert _detect_temporal_contradiction("Worked at DataCorp 2019", "") is False

    def test_uses_earliest_year_in_claim(self):
        """When claim has multiple years, earliest is used for comparison.
        Claim spans 2017-2020, founding 2018 → 2017 < 2018 → True."""
        claim_text = "Led DataCorp from 2017 to 2020"
        web_content = "DataCorp was launched in 2018."
        assert _detect_temporal_contradiction(claim_text, web_content) is True


# ── _build_new_claims_from_repos ──────────────────────────────────────────────

class TestBuildNewClaimsFromRepos:
    """WHY: Auto-discovered GitHub repos are Tier A signals not mentioned in the CV.
    The cap, star filter, and dedup logic must be verified independently."""

    def _repo(self, name: str, stars: int = 50) -> dict:
        return {
            "name": name,
            "stargazers_count": stars,
            "html_url": f"https://github.com/testuser/{name}",
            "description": f"{name} description",
        }

    def test_builds_claim_for_starred_repo(self):
        """Repo with stars produces a Tier A claim with verification attached."""
        repos = [self._repo("awesome-lib", stars=42)]
        claims = _build_new_claims_from_repos("testuser", repos, [])
        assert len(claims) == 1
        assert claims[0].tier == "A"
        assert "awesome-lib" in claims[0].text
        assert claims[0].verification is not None
        assert claims[0].verification.source == VerificationSource.GITHUB_API

    def test_skips_zero_star_repos(self):
        """Repos with 0 stars are not included — no external signal value."""
        repos = [self._repo("personal-notes", stars=0)]
        claims = _build_new_claims_from_repos("testuser", repos, [])
        assert len(claims) == 0

    def test_skips_repo_already_in_existing_claims(self):
        """If existing claims already reference the repo, don't duplicate."""
        existing = [_make_claim(text="Built awesome-lib on GitHub", tier="B")]
        repos = [self._repo("awesome-lib", stars=100)]
        claims = _build_new_claims_from_repos("testuser", repos, existing)
        assert len(claims) == 0

    def test_respects_settings_cap(self):
        """No more than settings.max_new_claims_from_github claims produced."""
        from screen.core.config import settings

        repos = [self._repo(f"repo-{i}", stars=10 + i) for i in range(10)]
        claims = _build_new_claims_from_repos("testuser", repos, [])
        assert len(claims) <= settings.max_new_claims_from_github

    def test_returns_empty_list_for_empty_repos(self):
        """Empty repos list → empty result, no error."""
        claims = _build_new_claims_from_repos("testuser", [], [])
        assert claims == []

    def test_verification_contains_repo_url(self):
        """Verification result must include the repo URL for the audit trail."""
        repos = [self._repo("cool-project", stars=5)]
        claims = _build_new_claims_from_repos("testuser", repos, [])
        assert claims[0].verification.url == "https://github.com/testuser/cool-project"


# ── _verify_claim_via_github ──────────────────────────────────────────────────

class TestVerifyClaimViaGithub:
    """WHY: The B→A upgrade is the most impactful single action in verify_claims.
    We must verify that the upgrade happens when repos are present and that
    the function degrades gracefully when repos is empty."""

    def _github_claim(self, tier: str = "B") -> Claim:
        return Claim(
            text="Contributed to open source project with 500 stars on GitHub",
            tier=tier,
            confidence_weight=SIGNAL_WEIGHTS[tier],
            source_location="GitHub contribution claim",
            is_verifiable_externally=True,
        )

    def _repo(self, name: str = "oss-project", stars: int = 500) -> dict:
        return {
            "name": name,
            "stargazers_count": stars,
            "html_url": f"https://github.com/testuser/{name}",
        }

    def test_upgrades_tier_b_to_a_when_repos_found(self):
        """GitHub repos present → Tier B claim upgraded to Tier A."""
        claim = self._github_claim(tier="B")
        result = _verify_claim_via_github(claim, "testuser", [self._repo()])
        assert result.tier == "A"
        assert result.confidence_weight == SIGNAL_WEIGHTS["A"]

    def test_verification_records_tier_change(self):
        """VerificationResult.tier_change must be 'B->A' after upgrade."""
        claim = self._github_claim(tier="B")
        result = _verify_claim_via_github(claim, "testuser", [self._repo()])
        assert result.verification is not None
        assert result.verification.tier_change == "B->A"

    def test_no_upgrade_when_repos_empty(self):
        """Empty repos list → claim tier unchanged, verification still attached."""
        claim = self._github_claim(tier="B")
        result = _verify_claim_via_github(claim, "testuser", [])
        assert result.tier == "B"

    def test_non_b_tier_claim_not_upgraded(self):
        """Tier C claim is not upgraded to A even if repos found."""
        claim = self._github_claim(tier="C")
        result = _verify_claim_via_github(claim, "testuser", [self._repo()])
        assert result.tier == "C"

    def test_returns_claim_with_verification_attached(self):
        """Result claim must always have verification set."""
        claim = self._github_claim(tier="B")
        result = _verify_claim_via_github(claim, "testuser", [self._repo()])
        assert result.verification is not None
        assert result.verification.source == VerificationSource.GITHUB_API


# ── verify_claims_node (integration, mocked) ──────────────────────────────────

class TestVerifyClaimsNode:
    """WHY: The node function orchestrates all external calls and updates
    the ScreeningState. Judges running `pytest` should be able to verify
    the node's contract without API keys."""

    def test_returns_required_state_keys(self):
        """Node must return evidence_bundle, trajectory, and total_cost_usd."""
        state = _make_state()
        with (
            patch("screen.agent.nodes.verify_claims._fetch_github_repos", return_value=[]),
            patch("screen.agent.nodes.verify_claims._tavily_search", return_value=[]),
            patch("screen.agent.nodes.verify_claims._fetch_portfolio_text", return_value=""),
        ):
            result = verify_claims_node(state)

        assert "evidence_bundle" in result
        assert "trajectory" in result
        assert "total_cost_usd" in result

    def test_trajectory_entry_is_list(self):
        """trajectory value must be a list (operator.add reducer in state)."""
        state = _make_state()
        with (
            patch("screen.agent.nodes.verify_claims._fetch_github_repos", return_value=[]),
            patch("screen.agent.nodes.verify_claims._tavily_search", return_value=[]),
            patch("screen.agent.nodes.verify_claims._fetch_portfolio_text", return_value=""),
        ):
            result = verify_claims_node(state)

        assert isinstance(result["trajectory"], list)
        assert len(result["trajectory"]) == 1

    def test_node_upgrades_github_claim_when_repos_available(self):
        """When GitHub API returns repos, Tier B GitHub claims are upgraded to A."""
        github_claim = Claim(
            text="Open source repo with 100 stars on GitHub",
            tier="B",
            confidence_weight=SIGNAL_WEIGHTS["B"],
            source_location="github.com/testuser/myrepo",
            is_verifiable_externally=True,
        )
        cv_with_github = (
            "Jane Smith — Python engineer. github.com/testuser — open source contributor. "
            "Built payment APIs, led 5-person team. Python, Go, Kafka, PostgreSQL."
        )
        state = _make_state(cv_text=cv_with_github)
        state["evidence_bundle"] = _make_bundle(claims=[github_claim])

        mock_repos = [
            {
                "name": "myrepo",
                "stargazers_count": 100,
                "html_url": "https://github.com/testuser/myrepo",
            }
        ]

        with (
            patch("screen.agent.nodes.verify_claims._fetch_github_repos", return_value=mock_repos),
            patch("screen.agent.nodes.verify_claims._tavily_search", return_value=[]),
            patch("screen.agent.nodes.verify_claims._fetch_portfolio_text", return_value=""),
        ):
            result = verify_claims_node(state)

        updated_bundle = result["evidence_bundle"]
        upgraded = [c for c in updated_bundle.claims if c.verification and c.verification.tier_change == "B->A"]
        assert len(upgraded) >= 1

    def test_node_handles_missing_evidence_bundle_gracefully(self):
        """If evidence_bundle is None, node should raise StateTransitionError."""
        from screen.core.exceptions import StateTransitionError

        state = _make_state()
        state["evidence_bundle"] = None

        with pytest.raises(StateTransitionError):
            verify_claims_node(state)

    def test_cost_is_zero(self):
        """verify_claims makes no LLM calls — total_cost_usd returned must be 0."""
        state = _make_state()
        with (
            patch("screen.agent.nodes.verify_claims._fetch_github_repos", return_value=[]),
            patch("screen.agent.nodes.verify_claims._tavily_search", return_value=[]),
            patch("screen.agent.nodes.verify_claims._fetch_portfolio_text", return_value=""),
        ):
            result = verify_claims_node(state)

        assert result["total_cost_usd"] == 0.0
