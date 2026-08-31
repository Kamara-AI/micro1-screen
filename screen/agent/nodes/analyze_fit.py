"""
WHY: Node 4 — the multi-dimensional assessor. This is where SCREEN implements
the "senior recruiter mental model" most completely. Rather than one score,
we produce six independently-reasoned dimension scores that each capture a
different axis of fit.

The critical design principle here: the LLM evaluates each dimension INDEPENDENTLY.
This prevents the halo effect — a candidate with outstanding technical skills
shouldn't automatically score high on learning velocity or career trajectory.
Each dimension score must be backed by a rationale referencing specific evidence.

The six mental models this node implements:
  1. Achievement pattern reader (technical_fit + experience_level_fit)
  2. Career trajectory analyst (career_shape + career_velocity)
  3. Learning agility evaluator (learning_velocity_score — Bock's top predictor)
  4. Builder/maintainer classifier (builder_maintainer_score)
  5. Company context reader (company_contexts — title meaning varies with company size)
  6. Non-obvious fit detector (non_obvious_fit_signals — what ATS misses)

HOW: Gemini Pro with structured output bound to FitAnalysis. We pass both the
EvidenceBundle (structured evidence with quality tiers) AND the CandidateProfile
so the LLM has the full picture without seeing raw CV text.
"""

import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from screen.core.config import settings
from screen.core.exceptions import LLMCallError, StateTransitionError
from screen.core.llm_factory import build_llm, get_active_model
from screen.core.logging_config import get_logger
from screen.core.trajectory import estimate_token_cost, make_trajectory_entry
from screen.schemas.analysis import FitAnalysis
from screen.schemas.candidate import CandidateProfile
from screen.schemas.evidence import EvidenceBundle
from screen.schemas.state import ScreeningState

logger = get_logger(__name__)

# ── System prompt ──────────────────────────────────────────────────────────────
ANALYZE_FIT_SYSTEM_PROMPT = """You are a senior technical recruiter. Produce a FitAnalysis by scoring five dimensions independently (0.0–1.0 each). No halo effect: each dimension is scored on its own evidence only.

━━━ PRIORITY ZERO — CHECK BEFORE ALL SCORING ━━━

P0. DOMAIN MISMATCH (operations/supply-chain roles):
Apply the hard cap ONLY if the candidate's ENTIRE career is in one of these
FUNDAMENTALLY DIFFERENT operations domains (these do NOT transfer to FMCG supply chain):
  - Events/conferences/venue operations
  - Contact centre / customer service operations
  - NGO / programme management / M&E
  - Financial / payment / settlement operations
  - Banking branch operations

If their background is in ANY of those domains with zero supply-chain vocabulary:
  • technical_fit = 0.05
  • experience_level_fit = 0.15
  • These are hard caps — not starting points. Do not round up.
  State the domain gap explicitly in technical_fit_rationale.

NOTE: Hotel/hospitality operations is NOT a hard-cap domain — it has some management
transferability. Score it naturally but apply a proportionate domain gap penalty.
A supply-chain keywords = 0 silence flag signals a gap but does NOT alone trigger the hard cap.

P1. PRE-COMPUTED FACTS (appear in evidence bundle):
The evidence bundle may contain "DETERMINISTIC PRE-COMPUTED FACTS" from Python analysis.
These are ground truth. If they note:
  • Supervision language >70% → reduce experience_level_fit by at least 0.3
  • Production deployment NOT DETECTED → experience_level_fit ≤ 0.3 for senior ML/DS roles
  • Skill-level conflicts → the contradictions are already in the bundle; weight them heavily

━━━ DIMENSION SCORING RULES ━━━

1. TECHNICAL FIT (technical_fit, weight 35% of composite):
   1.0 = every key technical requirement in Tier A or B evidence
   0.7 = most requirements evidenced; minor learnable gaps
   0.5 = partial match; 1-2 key requirements missing
   0.3 = fundamental gap requiring significant ramp-up
   0.0 = no technical match
   Rule: use evidence TIERS, not skills_stated. Stated ≠ demonstrated.

2. EXPERIENCE LEVEL FIT (experience_level_fit, weight 25%):
   Score on SCOPE and OWNERSHIP, not years.
   A 4-year engineer who owned a 500K-user system may outrank an 8-year engineer in support.
   Academic/supervised research ≠ production ownership for a senior role.
   If ALL experience is academic/supervised with no production deployment: max 0.25.

3. LEARNING VELOCITY (learning_velocity_score, weight 25%):
   0.8–1.0 = demonstrable new domain entry per role, self-directed learning in production
   0.5–0.7 = some skill acquisition, mostly within comfort zone
   0.2–0.4 = same skillset many years, no reach
   0.0 = active stagnation

4. BUILDER/MAINTAINER (builder_maintainer_score, weight 15%):
   1.0 = pure builder (shipped, launched, zero-to-one throughout)
   0.5 = hybrid
   0.0 = pure maintainer (oversight, stability, no creation verbs)
   Score FIT to the role need: early startups want 0.8+; ops/maintenance roles want 0.2.

5. CAREER SHAPE (career_shape — pick ONE):
   ascending | accelerating | plateau | lateral | descending | non_linear

━━━ COMPANY CONTEXTS ━━━

For each role: estimate company size (micro/small/medium/large/enterprise).
Flag role_scope_appropriate=False when stated scope exceeds what company size supports
(e.g., "VP managing 50 people" at a 5-person company).

━━━ NON-OBVIOUS FIT SIGNALS ━━━

Look for what ATS would miss:
- Non-linear path with coherent arc
- Cross-domain skills directly applicable to this role
- Building track record without matching titles
- Community signals: open source, writing, talks

━━━ PROBE POINTS ━━━

State the single most material gap to verify in an interview.

━━━ BIAS PREVENTION ━━━

Do NOT use:
- University prestige as a signal
- Employment gaps as negatives without evidence
- Candidate name, location, or demographic indicators
- Brand-name employers over equivalent unknown companies
Do NOT penalise non-linear paths.

Output a complete FitAnalysis. Every score requires a rationale citing specific evidence."""

# ── LLM Setup ──────────────────────────────────────────────────────────────────
# WHY tier2: analyze_fit requires comparative scoring across multiple evidence
# claims against JD criteria — a genuine reasoning task, not extraction.
_llm = build_llm("tier2")
_structured_llm = _llm.with_structured_output(FitAnalysis)


@retry(
    stop=stop_after_attempt(settings.llm_max_retries),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _call_analyze_fit_llm(
    candidate_id: str,
    profile_summary: str,
    evidence_summary: str,
    job_description: str,
    role_seniority: str,
    role_type: str,
) -> FitAnalysis:
    """
    WHY: Isolated LLM call with retry. Passes both the structured profile and
    the evidence bundle summary — the LLM needs evidence tiers to produce
    defensible dimension scores.

    HOW: The evidence_summary provides the quality-weighted claim picture.
    The profile_summary provides the structural/trajectory context.
    Together they give the LLM everything a senior recruiter would have.
    """
    messages = [
        SystemMessage(content=ANALYZE_FIT_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"CANDIDATE ID: {candidate_id}\n"
                f"ROLE SENIORITY: {role_seniority}\n"
                f"ROLE TYPE: {role_type}\n\n"
                f"--- JOB DESCRIPTION ---\n{job_description}\n\n"
                f"--- CANDIDATE PROFILE (structured, anonymised) ---\n{profile_summary}\n\n"
                f"--- EVIDENCE BUNDLE (extracted claims with tiers) ---\n{evidence_summary}\n\n"
                f"Produce the complete FitAnalysis for this candidate."
            )
        ),
    ]
    result: FitAnalysis = _structured_llm.invoke(messages)
    return result


def _render_evidence_for_llm(evidence_bundle: EvidenceBundle) -> str:
    """
    WHY: Structured text rendering of the EvidenceBundle for the LLM.
    Provides the quality-tiered evidence picture without exposing raw CV text.
    """
    lines = [
        f"TOTAL WEIGHTED SCORE: {evidence_bundle.total_weighted_score:.2f}",
        f"SILENCE PENALTY: {evidence_bundle.silence_penalty:.2f}",
        f"BUILDER/MAINTAINER: {evidence_bundle.builder_maintainer_verdict}",
        f"CRITICAL CONTRADICTION: {evidence_bundle.has_critical_contradiction}",
        f"UNVERIFIABLE HIGH-STAKES CLAIM: {evidence_bundle.has_unverifiable_high_stakes_claim}",
        "",
        "CLAIMS (with tiers and weights):",
    ]

    for i, claim in enumerate(evidence_bundle.claims):
        lines.append(
            f"  [{i}] Tier {claim.tier} (weight {claim.confidence_weight:+.1f}) — "
            f"{claim.text} "
            f"[source: {claim.source_location}] "
            f"[externally verifiable: {claim.is_verifiable_externally}]"
        )

    if evidence_bundle.contradictions:
        lines.append("")
        lines.append("CONTRADICTIONS:")
        for i, contra in enumerate(evidence_bundle.contradictions):
            lines.append(
                f"  [{i}] {contra.severity.upper()} — {contra.contradiction_type}: "
                f"{contra.explanation}"
            )

    if evidence_bundle.silence_flags:
        lines.append("")
        lines.append("SILENCE FLAGS:")
        for i, flag in enumerate(evidence_bundle.silence_flags):
            lines.append(
                f"  [{i}] {flag.severity.upper()} — Expected: {flag.expected_signal}. "
                f"Interpretation: {flag.absence_interpretation}"
            )

    if evidence_bundle.builder_signals:
        lines.append("")
        lines.append(f"BUILDER SIGNALS: {'; '.join(evidence_bundle.builder_signals)}")

    if evidence_bundle.maintainer_signals:
        lines.append(f"MAINTAINER SIGNALS: {'; '.join(evidence_bundle.maintainer_signals)}")

    return "\n".join(lines)


def _render_profile_summary_for_llm(candidate_profile: CandidateProfile) -> str:
    """
    WHY: Compact profile rendering for the fit analysis context. Less verbose
    than the evidence extraction rendering — at this point we need the shape
    and trajectory, not every bullet point.
    """
    lines = [
        f"Experience: {candidate_profile.total_years_experience or 'unknown'} years",
        f"Career start: {candidate_profile.career_start_year or 'unknown'}",
        f"Non-linear path: {candidate_profile.has_non_linear_path}",
        f"Education: {candidate_profile.highest_education_level}",
        "",
        "ROLE HISTORY:",
    ]
    for role in candidate_profile.roles:
        lines.append(
            f"  {role.title} @ {role.company} "
            f"({role.start_date or '?'} – {role.end_date or 'Present'}, "
            f"{role.duration_months or '?'} months) "
            f"[quantified: {role.is_quantified}]"
        )
    if candidate_profile.employment_gaps:
        lines.append("")
        lines.append("EMPLOYMENT GAPS:")
        for gap in candidate_profile.employment_gaps:
            lines.append(
                f"  {gap.gap_start} → {gap.gap_end} "
                f"({gap.duration_months or '?'} months) "
                f"[explained: {gap.explanation_provided}]"
            )
    return "\n".join(lines)


def analyze_fit_node(state: ScreeningState) -> dict[str, Any]:
    """
    WHY: Produces the multi-dimensional FitAnalysis that the decision node
    blends 40% with the evidence quality score to produce the final confidence %.

    HOW:
    1. Validate state has candidate_profile and evidence_bundle
    2. Render both to structured text summaries
    3. Call Gemini Pro for dimension-by-dimension analysis
    4. Build trajectory entry with composite score logged
    """
    node_name = "analyze_fit"
    start_ms = time.time() * 1000

    candidate_profile = state.get("candidate_profile")
    if candidate_profile is None:
        raise StateTransitionError(node_name, "candidate_profile")

    evidence_bundle = state.get("evidence_bundle")
    if evidence_bundle is None:
        raise StateTransitionError(node_name, "evidence_bundle")

    screening_input = state.get("screening_input")
    if screening_input is None:
        raise StateTransitionError(node_name, "screening_input")

    candidate_id = screening_input.candidate_id

    logger.info(
        "analyze_fit started",
        node=node_name,
        candidate_id=candidate_id,
    )

    profile_text = _render_profile_summary_for_llm(candidate_profile)
    evidence_text = _render_evidence_for_llm(evidence_bundle)

    try:
        fit_analysis = _call_analyze_fit_llm(
            candidate_id=candidate_id,
            profile_summary=profile_text,
            evidence_summary=evidence_text,
            job_description=screening_input.job_description,
            role_seniority=screening_input.role_seniority,
            role_type=screening_input.role_type,
        )
    except Exception as exc:
        raise LLMCallError(node_name, str(exc)) from exc

    # Estimate cost: combined input text is our token proxy
    prompt_token_estimate = (
        len(profile_text) + len(evidence_text) + len(screening_input.job_description)
    ) // 4
    completion_token_estimate = 800
    cost_usd = estimate_token_cost(
        prompt_tokens=prompt_token_estimate,
        completion_tokens=completion_token_estimate,
        model_tier=2,
    )

    composite = fit_analysis.composite_fit_score

    trajectory_entry = make_trajectory_entry(
        node=node_name,
        start_time_ms=start_ms,
        reasoning_summary=(
            f"Multi-dimensional fit analysis complete. "
            f"Technical fit: {fit_analysis.technical_fit:.2f}. "
            f"Experience level: {fit_analysis.experience_level_fit:.2f}. "
            f"Learning velocity: {fit_analysis.learning_velocity_score:.2f}. "
            f"Builder/maintainer: {fit_analysis.builder_maintainer_score:.2f}. "
            f"Composite score: {composite:.2f}. "
            f"Career shape: {fit_analysis.career_shape}. "
            f"Red flags: {len(fit_analysis.role_specific_red_flags)}. "
            f"Green flags: {len(fit_analysis.role_specific_green_flags)}."
        ),
        output_summary=(
            f"Composite fit: {composite:.2f} | "
            f"tech: {fit_analysis.technical_fit:.2f} | "
            f"velocity: {fit_analysis.learning_velocity_score:.2f} | "
            f"shape: {fit_analysis.career_shape}"
        ),
        evidence_keys=[f"dim:technical", "dim:experience", "dim:velocity", "dim:builder"],
        model_used=get_active_model("tier2"),
        cost_usd=cost_usd,
    )

    logger.info(
        "analyze_fit complete",
        node=node_name,
        candidate_id=candidate_id,
        composite_fit_score=round(composite, 3),
        technical_fit=round(fit_analysis.technical_fit, 3),
        learning_velocity=round(fit_analysis.learning_velocity_score, 3),
        career_shape=fit_analysis.career_shape,
        duration_ms=trajectory_entry.duration_ms,
        cost_usd=cost_usd,
    )

    return {
        "fit_analysis": fit_analysis,
        "trajectory": [trajectory_entry],
        "total_cost_usd": cost_usd,
    }
