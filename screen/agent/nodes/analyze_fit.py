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
ANALYZE_FIT_SYSTEM_PROMPT = """You are a senior technical recruiter with 15+ years of experience.
You specialise in multi-dimensional fit assessment, going far beyond keyword matching.

Your task: produce a FitAnalysis by evaluating the candidate's fit across FIVE independent
dimensions. You MUST evaluate each dimension separately — do not let your impression of one
dimension bias your score on another (this is the halo effect and we explicitly forbid it).

DIMENSION SCORING RULES (0.0 – 1.0 per dimension):

1. TECHNICAL FIT (technical_fit)
   - 1.0: Every key technical requirement is demonstrated in real work (Tier A or B evidence)
   - 0.7: Most requirements evidenced; minor gaps that are learnable
   - 0.5: Partial match; core skills present but 1-2 key requirements missing
   - 0.3: Fundamental technical gap that would require significant ramp-up
   - 0.0: No demonstrated match to technical requirements
   - Use EVIDENCE TIERS, not just skills_stated — stated ≠ demonstrated
   - technical_fit_rationale: cite specific claims and their tiers

2. EXPERIENCE LEVEL FIT (experience_level_fit)
   - Match the candidate's actual scope and autonomy to what the role requires
   - Do NOT use years as the primary signal — use scope, ownership, and decision authority
   - A 4-year engineer who owned a 500K-user system may fit a "senior" role better
     than an 8-year engineer who always worked in support functions
   - experience_level_rationale: cite scope evidence, not years

3. LEARNING VELOCITY (learning_velocity_score) — Bock's top performance predictor
   - High (0.8-1.0): Demonstrable new domain entry per role, self-directed learning applied
                     in production, promotion into unfamiliar territory
   - Medium (0.5-0.7): Some new skill acquisition but mostly within comfort zone
   - Low (0.2-0.4): Same skillset across many years, no evidence of reaching out of comfort zone
   - 0.0: Active stagnation signals
   - Populate learning_velocity_evidence with specific examples

4. BUILDER/MAINTAINER (builder_maintainer_score)
   - 1.0 = pure builder: shipping, launching, zero-to-one creation language throughout
   - 0.5 = hybrid: mix of build and maintain signals
   - 0.0 = pure maintainer: oversight, management, stability, no creation verbs
   - Match to ROLE NEED: early startups want 0.8+; enterprise ops roles want 0.0-0.3
   - Do not penalise maintainers for maintenance roles — assess FIT not absolute value

5. CAREER SHAPE (career_shape — pick ONE):
   ascending: steady scope increases and title growth
   accelerating: unusually fast advancement (verify: real or title inflation?)
   plateau: similar level/scope for 8+ years (specialist is ok; stuck is a flag)
   lateral: cross-functional moves without clear ascent
   descending: Director→Manager-type moves (strategic downshift or concerning?)
   non_linear: multiple domain pivots showing learning agility

COMPANY CONTEXT (for each role in company_contexts):
   - estimated_size: micro<10, small 10-50, medium 50-500, large 500-5K, enterprise 5K+
   - role_scope_appropriate: False when stated scope exceeds what company size supports

NON-OBVIOUS FIT SIGNALS:
   Look for signals that an ATS would penalise or miss:
   - Non-linear path with coherent narrative arc (each pivot made sense given the previous)
   - Cross-domain skills directly applicable to this role (e.g. ops background for platform eng role)
   - Building track record without matching job titles (IC who shipped without "architect" title)
   - Community signals: open source, technical writing, conference talks

PROBE POINTS (for the interviewer brief):
   - What would you most need to verify in an interview about this candidate?
   - What's the gap that is most material to this role?

BIAS PREVENTION — you MUST NOT:
   - Use university prestige as a positive signal (where you went ≠ what you can do)
   - Penalise non-linear paths (they correlate with learning agility)
   - Interpret employment gaps as negative without specific evidence of a problem
   - Weight candidate name, location, or demographic indicators
   - Prefer experience at brand-name companies over equivalent work at unknown companies

Output a complete FitAnalysis with ALL fields populated. Every score must have a rationale."""

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
