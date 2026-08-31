"""
WHY: Node 7 — the ESCALATE path only. When the decision engine escalates a
candidate, the human reviewer should receive a structured brief — not just a flag.

This is the feature that no ATS and no existing AI screener produces. Every
tool we know of either passes or fails candidates. When they escalate, they say
"review this". We say: here is EXACTLY what to verify, how to verify it, and
what to ask first.

The HumanBrief implements three senior recruiter habits:
  1. "What do I know for certain?" → what_we_know (Tier A + strong Tier B claims)
  2. "What do I need to verify before I decide?" → what_we_cannot_verify + verification_tasks
  3. "What's the first question I'd ask in the interview?" → first_question + risk_to_probe

WHY current_tier becomes 3 here: The human reviewer is now part of the process.
Tier 3 = human-in-the-loop. This is the escalation brief tier.

HOW: Gemini Pro (Tier 3 model) reads the EvidenceBundle, FitAnalysis, and Decision
and generates a structured HumanBrief. The LLM is not making a decision — it is
synthesising the evidence into a human-readable brief.
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
from screen.schemas.decision import Decision, HumanBrief
from screen.schemas.evidence import EvidenceBundle
from screen.schemas.state import ScreeningState

logger = get_logger(__name__)

# ── System prompt ──────────────────────────────────────────────────────────────
BUILD_HUMAN_BRIEF_SYSTEM_PROMPT = """You are a senior technical recruiter writing a structured escalation brief
for a human hiring manager. The AI agent has flagged this candidate for human review.

Your job is to synthesise the evidence into a brief that tells the reviewer:
1. What we know with confidence (Tier A and strong Tier B evidence)
2. What we cannot verify (specific claims that are material but unverifiable)
3. What actions to take before deciding (concrete verification tasks)
4. What to ask in the interview (evidence-based, targeted questions)
5. What the first question should be (the most critical opening)
6. What risk to probe (the thing that would likely disqualify if true)

WRITING STANDARDS:
- Be specific. "Check LinkedIn for DataCorp founding date" not "verify employment history"
- Be honest about uncertainty. "We cannot confirm X without Y" not "X seems questionable"
- No platitudes. Every sentence should give the reviewer something to DO
- summary: max 2 sentences — what the agent found and why it cannot make the call
- No raw CV text in the brief — paraphrase and reference ("Role at Company, dates")

WHAT_WE_KNOW: Only claims the agent rated Tier A or strong Tier B (specific, plausible,
internally consistent). These are the foundations the reviewer can build on.

WHAT_WE_CANNOT_VERIFY: Specific claims that are material to the verdict (not just any
unverifiable claim — only those that MATTER for this role). Include WHY they matter.

VERIFICATION_TASKS: Concrete, external steps. Examples:
  - "Check Companies House / Crunchbase for [Company] founding date to verify timeline"
  - "Search LinkedIn for the candidate's profile and verify role dates"
  - "Check Credly or AWS certification registry if a certification badge link is provided"
  - "Ask for GitHub profile and verify repo contribution dates and authorship"

SUGGESTED_INTERVIEW_QUESTIONS: 3-5 questions that directly probe the specific gaps
identified. Each question should reference the specific gap it's probing.
Example: "You described leading a team of 20 engineers at [Company] — can you walk me
through how that team was structured and who your direct reports were?"

FIRST_QUESTION: The single most important question. This should target the most
material gap or the primary escalation trigger (contradiction / unverifiable claim).
Frame it as a genuine invitation, not an interrogation.

RISK_TO_PROBE: The one thing that — if it turns out to be true — would likely
disqualify this candidate. Surface it early in the interview. Be specific.

Output the complete HumanBrief. It must be actionable and honest."""

# ── LLM Setup ──────────────────────────────────────────────────────────────────
# WHY tier3: the human brief is synthesised narrative for a hiring manager.
# It requires coherent reasoning across contradictions, verified claims, and
# bias flags — and must read as something a human would sign their name to.
_llm = build_llm("tier3")
_structured_llm = _llm.with_structured_output(HumanBrief)


@retry(
    stop=stop_after_attempt(settings.llm_max_retries),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _call_build_brief_llm(
    candidate_id: str,
    evidence_summary: str,
    fit_summary: str,
    decision_summary: str,
    escalation_category: str,
) -> HumanBrief:
    """
    WHY: The brief is generated from the structured evidence and fit summaries —
    never from raw CV text. This preserves the data boundary and ensures the
    brief is grounded in verified, quality-tiered evidence rather than raw claims.

    HOW: We pass the escalation_category explicitly so the LLM knows WHY
    escalation was triggered and can orient the brief accordingly.
    """
    messages = [
        SystemMessage(content=BUILD_HUMAN_BRIEF_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"CANDIDATE ID: {candidate_id}\n"
                f"ESCALATION CATEGORY: {escalation_category}\n\n"
                f"--- DECISION (why this was escalated) ---\n{decision_summary}\n\n"
                f"--- EVIDENCE BUNDLE (quality-tiered claims) ---\n{evidence_summary}\n\n"
                f"--- FIT ANALYSIS ---\n{fit_summary}\n\n"
                f"Generate the complete HumanBrief for the reviewer."
            )
        ),
    ]
    result: HumanBrief = _structured_llm.invoke(messages)
    return result


def _render_decision_for_brief(decision: Decision) -> str:
    """WHY: Compact decision summary for the brief context."""
    lines = [
        f"VERDICT: {decision.verdict}",
        f"CONFIDENCE: {decision.confidence_pct}%",
        f"ESCALATION REASON: {decision.escalation_reason or 'N/A'}",
        "",
        "PRIMARY EVIDENCE CITED:",
    ]
    for evidence in decision.primary_evidence:
        lines.append(f"  - {evidence}")
    return "\n".join(lines)


def _render_evidence_for_brief(evidence_bundle: EvidenceBundle) -> str:
    """WHY: Evidence summary focused on what the human reviewer needs for the brief."""
    lines = [
        f"TOTAL WEIGHTED SCORE: {evidence_bundle.total_weighted_score:.2f}",
        f"CRITICAL CONTRADICTION: {evidence_bundle.has_critical_contradiction}",
        f"UNVERIFIABLE HIGH-STAKES CLAIM: {evidence_bundle.has_unverifiable_high_stakes_claim}",
        "",
        "TIER A + B CLAIMS (verified and stated — what we know):",
    ]
    for claim in evidence_bundle.claims:
        if claim.tier in ("A", "B"):
            lines.append(
                f"  [Tier {claim.tier}] {claim.text} "
                f"[{claim.source_location}] "
                f"[verifiable: {claim.is_verifiable_externally}]"
            )

    if evidence_bundle.contradictions:
        lines.append("")
        lines.append("CONTRADICTIONS (what requires investigation):")
        for contra in evidence_bundle.contradictions:
            lines.append(
                f"  [{contra.severity.upper()}] {contra.contradiction_type}: "
                f"{contra.explanation}"
            )

    return "\n".join(lines)


def _render_fit_for_brief(fit_analysis: FitAnalysis) -> str:
    """WHY: Fit summary showing scores and key flags for the brief context."""
    lines = [
        f"COMPOSITE FIT: {fit_analysis.composite_fit_score:.2f}",
        f"TECHNICAL: {fit_analysis.technical_fit:.2f} — {fit_analysis.technical_fit_rationale}",
        f"EXPERIENCE: {fit_analysis.experience_level_fit:.2f} — {fit_analysis.experience_level_rationale}",
        f"LEARNING VELOCITY: {fit_analysis.learning_velocity_score:.2f} — {fit_analysis.learning_velocity_rationale}",
        f"CAREER SHAPE: {fit_analysis.career_shape}",
        "",
        "PROBE POINTS:",
    ]
    for point in fit_analysis.probe_points:
        lines.append(f"  - {point}")

    if fit_analysis.has_bias_flag:
        lines.append("")
        lines.append("BIAS FLAGS DETECTED:")
        for flag in fit_analysis.bias_flags:
            lines.append(f"  - {flag}")

    return "\n".join(lines)


def build_human_brief_node(state: ScreeningState) -> dict[str, Any]:
    """
    WHY: Generates the structured escalation brief for the human reviewer.
    Only runs when should_escalate=True (enforced by graph routing).

    HOW:
    1. Validate state has evidence_bundle, fit_analysis, and decision
    2. Render each to a structured text summary
    3. Call Gemini Pro to generate the HumanBrief
    4. Set current_tier=3 to signal human-in-the-loop escalation tier
    """
    node_name = "build_human_brief"
    start_ms = time.time() * 1000

    evidence_bundle = state.get("evidence_bundle")
    if evidence_bundle is None:
        raise StateTransitionError(node_name, "evidence_bundle")

    fit_analysis = state.get("fit_analysis")
    if fit_analysis is None:
        raise StateTransitionError(node_name, "fit_analysis")

    decision = state.get("decision")
    if decision is None:
        raise StateTransitionError(node_name, "decision")

    screening_input = state.get("screening_input")
    if screening_input is None:
        raise StateTransitionError(node_name, "screening_input")

    candidate_id = screening_input.candidate_id
    escalation_category = decision.escalation_category or "ambiguous_non_linear_background"

    logger.info(
        "build_human_brief started",
        node=node_name,
        candidate_id=candidate_id,
        escalation_category=escalation_category,
    )

    evidence_text = _render_evidence_for_brief(evidence_bundle)
    fit_text = _render_fit_for_brief(fit_analysis)
    decision_text = _render_decision_for_brief(decision)

    try:
        human_brief = _call_build_brief_llm(
            candidate_id=candidate_id,
            evidence_summary=evidence_text,
            fit_summary=fit_text,
            decision_summary=decision_text,
            escalation_category=escalation_category,
        )
    except Exception as exc:
        raise LLMCallError(node_name, str(exc)) from exc

    prompt_token_estimate = (
        len(evidence_text) + len(fit_text) + len(decision_text)
    ) // 4
    completion_token_estimate = 600
    cost_usd = estimate_token_cost(
        prompt_tokens=prompt_token_estimate,
        completion_tokens=completion_token_estimate,
        model_tier=3,
    )

    num_questions = len(human_brief.suggested_interview_questions)
    num_tasks = len(human_brief.verification_tasks)

    trajectory_entry = make_trajectory_entry(
        node=node_name,
        start_time_ms=start_ms,
        reasoning_summary=(
            f"Human brief generated for escalated candidate. "
            f"Escalation category: {escalation_category}. "
            f"{len(human_brief.what_we_know)} verified items, "
            f"{len(human_brief.what_we_cannot_verify)} unverifiable claim(s). "
            f"{num_tasks} verification task(s), "
            f"{num_questions} interview question(s) generated."
        ),
        output_summary=(
            f"HumanBrief: {escalation_category} | "
            f"{num_tasks} tasks | {num_questions} questions"
        ),
        evidence_keys=["human_brief:what_we_know", "human_brief:verification_tasks"],
        model_used=get_active_model("tier3"),
        cost_usd=cost_usd,
    )

    logger.info(
        "build_human_brief complete",
        node=node_name,
        candidate_id=candidate_id,
        escalation_category=escalation_category,
        num_verification_tasks=num_tasks,
        num_interview_questions=num_questions,
        duration_ms=trajectory_entry.duration_ms,
        cost_usd=cost_usd,
    )

    return {
        "human_brief": human_brief,
        "current_tier": 3,
        "trajectory": [trajectory_entry],
        "total_cost_usd": cost_usd,
    }
