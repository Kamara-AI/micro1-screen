"""
WHY: Node 3 — the intelligence core. This is what makes SCREEN different from
every ATS and keyword-matcher. Rather than scoring a CV against a job description,
we extract structured evidence with quality tiers attached to each claim.

The distinction:
  - ATS: "Python mentioned 5 times → +5 points"
  - SCREEN: "Led Python backend serving 1M+ requests/day (Tier A, weight 1.0);
             'Proficient in Python' on skills list with no demonstrated projects (Tier C, weight 0.3)"

The evidence quality tier (A/B/C/D) is what makes the downstream confidence
calculation defensible. A candidate with 3 Tier A claims outscores one with
20 Tier C claims — as it should be.

HOW: Gemini Pro is used here (not Flash) because this requires nuanced reasoning
about claim credibility, contradiction detection, and silence pattern recognition.
The LLM output is validated against EvidenceBundle schema automatically.
"""

import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import retry, stop_after_attempt, wait_exponential

from screen.core.config import settings
from screen.core.exceptions import LLMCallError, StateTransitionError
from screen.core.logging_config import get_logger
from screen.core.trajectory import estimate_token_cost, make_trajectory_entry
from screen.schemas.evidence import SIGNAL_WEIGHTS, EvidenceBundle
from screen.schemas.state import ScreeningState

logger = get_logger(__name__)

# ── System prompt ──────────────────────────────────────────────────────────────
EXTRACT_EVIDENCE_SYSTEM_PROMPT = """You are an expert technical recruiter with elite evidence extraction skills.

Your task is to analyse a candidate's structured profile against a job description
and extract an EvidenceBundle — structured evidence with quality tiers.

SIGNAL TIER DEFINITIONS (assign these to every Claim):
  A (weight: 1.0)  — VERIFIED: Publicly cross-referenceable (GitHub repo URL, company still operating,
                     award with public record, named product). The claim CAN be checked independently.
  B (weight: 0.7)  — STATED: Specific, plausible, internally consistent, no contradictions.
                     Not externally verifiable but well-evidenced (named project with team + outcome).
  C (weight: 0.3)  — VAGUE: Generic language. "Worked on projects", "collaborated with teams",
                     "responsible for", "helped with" — no specifics, no numbers, no outcomes.
  D (weight: -1.5) — CONTRADICTED: This claim conflicts with another claim in the CV
                     (impossible dates, scope that exceeds company size, expert claim with no application).

SIGNAL_WEIGHTS map (you MUST assign confidence_weight from this map based on tier):
  "A" -> 1.0
  "B" -> 0.7
  "C" -> 0.3
  "D" -> -1.5

WHAT TO EXTRACT:

CLAIMS: Every material claim about skills, experience, or achievements.
  - source_location: "Role at [Company], [dates], bullet N" — never verbatim CV text
  - is_verifiable_externally: True only if claim could be checked against public data

CONTRADICTIONS: Look for:
  - temporal: impossible date overlaps, working at company before it was founded
  - scope_inflation: VP/Director title at 5-person startup managing stated 0 people
  - skill_level: "Expert in X" with no demonstrated application of X anywhere
  - title_inflation: Senior title with only junior task descriptions
  - employment_gap: Unexplained gap between two stated dates

SILENCE FLAGS: What's ABSENT that SHOULD be present given role type and seniority?
  - Senior engineers: no architectural decisions mentioned? Flag it.
  - People managers: no team size ever stated? Flag it.
  - Product roles: no product launches, no metrics? Flag it.
  - Quantified outcomes: for senior+ roles, absence of numbers IS a signal.

BUILDER vs MAINTAINER:
  Builder signals: "built from scratch", "launched", "zero to one", "architected X",
                   "founded", quantified growth they drove, shipped products
  Maintainer signals: "managed", "maintained", "oversaw", "ensured", "supported",
                      "responsible for ongoing", no ownership language, no creation verbs

BOOLEAN FLAGS:
  has_critical_contradiction: True if ANY contradiction has severity="critical"
  has_unverifiable_high_stakes_claim: True if a B/C tier claim is both:
    (a) high-impact for this specific role verdict AND
    (b) cannot be checked against public data

DO NOT:
  - Penalise non-linear career paths
  - Flag employment gaps as negative without context
  - Use prestige heuristics (Tier A universities, brand-name employers)
  - Generate claims not in the profile
  - Include raw CV text in source_location (paraphrase only)

The job description context is used to determine what silences are meaningful
and what claims are high-stakes. Tailor your analysis to the specific role.

Output the complete EvidenceBundle. Be thorough — a thin evidence bundle is
less defensible than a complete one with many C-tier claims accurately classified."""

# ── LLM Setup ──────────────────────────────────────────────────────────────────
_llm = ChatGoogleGenerativeAI(
    model=settings.gemini_model_tier2,
    google_api_key=settings.gemini_api_key,
    temperature=settings.llm_temperature,
)
_structured_llm = _llm.with_structured_output(EvidenceBundle)


@retry(
    stop=stop_after_attempt(settings.llm_max_retries),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _call_extract_evidence_llm(
    candidate_id: str,
    profile_summary: str,
    job_description: str,
    role_seniority: str,
    role_type: str,
) -> EvidenceBundle:
    """
    WHY: Isolated LLM call with retry. The profile_summary is a structured
    text rendering of CandidateProfile — never raw CV text, maintaining the
    data boundary established by parse_candidate.

    HOW: We pass both the structured profile and the job description so the
    LLM can reason about role-appropriate silences and high-stakes claims.
    """
    messages = [
        SystemMessage(content=EXTRACT_EVIDENCE_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"CANDIDATE ID: {candidate_id}\n"
                f"ROLE SENIORITY: {role_seniority}\n"
                f"ROLE TYPE: {role_type}\n\n"
                f"--- CANDIDATE PROFILE (structured, anonymised) ---\n"
                f"{profile_summary}\n\n"
                f"--- JOB DESCRIPTION ---\n"
                f"{job_description}\n\n"
                f"Extract the complete EvidenceBundle for this candidate."
            )
        ),
    ]
    result: EvidenceBundle = _structured_llm.invoke(messages)
    return result


def _render_profile_for_llm(candidate_profile: Any) -> str:
    """
    WHY: We pass a structured text rendering of CandidateProfile to the LLM
    rather than raw JSON. This is more readable for the model and ensures we
    never accidentally include raw CV text (which was already stripped in Node 1).

    HOW: Produces a structured plain-text summary. Company names remain because
    they are needed for contradiction detection (company founding dates, size).
    No candidate name appears — only "CANDIDATE".
    """
    lines = [
        f"CANDIDATE (anonymised) — {candidate_profile.total_years_experience or 'unknown'} years experience",
        f"Career start: {candidate_profile.career_start_year or 'unknown'}",
        f"Non-linear path: {candidate_profile.has_non_linear_path}",
        f"Highest education: {candidate_profile.highest_education_level}",
        "",
        "WORK HISTORY (reverse chronological):",
    ]

    for role in candidate_profile.roles:
        lines.append(
            f"  • {role.title} at {role.company} "
            f"({role.start_date or '?'} — {role.end_date or 'Present'}, "
            f"{role.duration_months or '?'} months)"
        )
        lines.append(f"    Quantified outcomes: {role.is_quantified}")
        if role.team_size_mentioned is not None:
            lines.append(f"    Team size mentioned: {role.team_size_mentioned}")
        for achievement in role.achievements:
            lines.append(f"    - {achievement}")

    if candidate_profile.education:
        lines.append("")
        lines.append("EDUCATION:")
        for edu in candidate_profile.education:
            lines.append(
                f"  • {edu.degree or 'Degree not stated'} in {edu.field_of_study or '?'} "
                f"at {edu.institution} "
                f"({'traditional' if edu.is_traditional else 'non-traditional'})"
            )

    if candidate_profile.skills_stated:
        lines.append("")
        lines.append(f"STATED SKILLS: {', '.join(candidate_profile.skills_stated)}")

    if candidate_profile.employment_gaps:
        lines.append("")
        lines.append("EMPLOYMENT GAPS:")
        for gap in candidate_profile.employment_gaps:
            explanation = "explained" if gap.explanation_provided else "NO EXPLANATION PROVIDED"
            lines.append(
                f"  • {gap.gap_start} to {gap.gap_end} "
                f"({gap.duration_months or '?'} months) — {explanation}"
            )

    return "\n".join(lines)


def extract_evidence_node(state: ScreeningState) -> dict[str, Any]:
    """
    WHY: This node produces the EvidenceBundle that drives all downstream scoring.
    The quality of this extraction directly determines the quality of the final verdict.

    HOW:
    1. Validate state has candidate_profile and screening_input
    2. Render profile to structured text (maintains data boundary — no raw CV)
    3. Call Gemini Pro with structured output bound to EvidenceBundle
    4. Log counts and key signals, build trajectory entry
    """
    node_name = "extract_evidence"
    start_ms = time.time() * 1000

    candidate_profile = state.get("candidate_profile")
    if candidate_profile is None:
        raise StateTransitionError(node_name, "candidate_profile")

    screening_input = state.get("screening_input")
    if screening_input is None:
        raise StateTransitionError(node_name, "screening_input")

    candidate_id = screening_input.candidate_id

    logger.info(
        "extract_evidence started",
        node=node_name,
        candidate_id=candidate_id,
    )

    profile_text = _render_profile_for_llm(candidate_profile)

    try:
        evidence_bundle = _call_extract_evidence_llm(
            candidate_id=candidate_id,
            profile_summary=profile_text,
            job_description=screening_input.job_description,
            role_seniority=screening_input.role_seniority,
            role_type=screening_input.role_type,
        )
    except Exception as exc:
        raise LLMCallError(node_name, str(exc)) from exc

    # Estimate cost: profile text + job description as proxy
    prompt_token_estimate = (len(profile_text) + len(screening_input.job_description)) // 4
    completion_token_estimate = len(evidence_bundle.claims) * 80 + 200
    cost_usd = estimate_token_cost(
        prompt_tokens=prompt_token_estimate,
        completion_tokens=completion_token_estimate,
        model_tier=2,
    )

    num_claims = len(evidence_bundle.claims)
    num_contradictions = len(evidence_bundle.contradictions)
    num_silence_flags = len(evidence_bundle.silence_flags)
    has_critical = evidence_bundle.has_critical_contradiction

    # Collect evidence keys for trajectory
    evidence_keys = (
        [f"claim:{i}" for i in range(num_claims)]
        + [f"contradiction:{i}" for i in range(num_contradictions)]
        + [f"silence:{i}" for i in range(num_silence_flags)]
    )

    trajectory_entry = make_trajectory_entry(
        node=node_name,
        start_time_ms=start_ms,
        reasoning_summary=(
            f"Extracted {num_claims} evidence claims "
            f"({sum(1 for c in evidence_bundle.claims if c.tier == 'A')} Tier A, "
            f"{sum(1 for c in evidence_bundle.claims if c.tier == 'B')} Tier B, "
            f"{sum(1 for c in evidence_bundle.claims if c.tier == 'C')} Tier C, "
            f"{sum(1 for c in evidence_bundle.claims if c.tier == 'D')} Tier D). "
            f"Found {num_contradictions} contradiction(s) "
            f"(critical: {has_critical}). "
            f"{num_silence_flags} silence flag(s) detected. "
            f"Builder/maintainer verdict: {evidence_bundle.builder_maintainer_verdict}."
        ),
        output_summary=(
            f"{num_claims} claims | {num_contradictions} contradictions "
            f"(critical: {has_critical}) | {num_silence_flags} silence flags | "
            f"verdict: {evidence_bundle.builder_maintainer_verdict}"
        ),
        evidence_keys=evidence_keys[:20],  # Cap at 20 keys for log readability
        model_used=settings.gemini_model_tier2,
        cost_usd=cost_usd,
    )

    logger.info(
        "extract_evidence complete",
        node=node_name,
        candidate_id=candidate_id,
        num_claims=num_claims,
        num_contradictions=num_contradictions,
        has_critical_contradiction=has_critical,
        builder_maintainer=evidence_bundle.builder_maintainer_verdict,
        duration_ms=trajectory_entry.duration_ms,
        cost_usd=cost_usd,
    )

    return {
        "evidence_bundle": evidence_bundle,
        "trajectory": [trajectory_entry],
        "total_cost_usd": cost_usd,
    }
