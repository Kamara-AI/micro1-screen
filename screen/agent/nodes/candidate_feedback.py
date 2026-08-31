"""
WHY: Node 8 — the candidate dignity protocol. Every candidate receives feedback,
regardless of verdict. This is both an ethical practice and a product differentiator.

No existing ATS or AI screener provides candidate feedback. They silently reject.
SCREEN gives every candidate:
  1. One genuine, specific strength (not a platitude)
  2. One honest, specific gap for THIS role (not a generic "lack of experience")
  3. Optional encouragement (ONLY when the gap is genuinely closable)

The design constraints matter:
  - genuine_strength must reference something concrete from the evidence
  - gap_for_this_role must explain WHY this specific role wasn't a match
  - encouragement is None for fundamental mismatches (misleading to say "you can get there")
  - The feedback is written as if the candidate could read it — because eventually they might

WHY Gemini Flash (not Pro): Feedback generation is not analytical reasoning — it's
clear, empathetic communication grounded in evidence we've already extracted.
Flash is sufficient and cheaper, keeping per-candidate cost low.

HOW: We pass the decision verdict, the EvidenceBundle's top claims, and the
FitAnalysis gap signals. The LLM generates feedback grounded in real evidence —
no hallucinated strengths or vague gaps.
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
from screen.schemas.decision import CandidateFeedback
from screen.schemas.state import ScreeningState

logger = get_logger(__name__)

# ── System prompt ──────────────────────────────────────────────────────────────
CANDIDATE_FEEDBACK_SYSTEM_PROMPT = """You are writing candidate feedback on behalf of a recruitment process.
The feedback will be sent to the candidate. Write it with respect and honesty.

You will receive:
- The verdict (STRONG_YES / YES / AMBIGUOUS / NO / STRONG_NO / ESCALATE)
- The top evidence claims from the candidate's profile
- The specific gaps identified in the fit analysis
- The role type and seniority level

RULES:

GENUINE_STRENGTH (required, min 20 characters):
  - Must reference something SPECIFIC from the evidence — not a platitude
  - Bad: "You seem passionate about technology"
  - Bad: "Your experience is impressive"
  - Good: "Your self-taught transition from operations to Python engineering, demonstrated
           across multiple shipped projects, is strong evidence of learning agility"
  - Good: "Building and scaling a payment API serving 50K+ daily transactions at an
           early-stage startup shows the kind of ownership experience that's rare to find"

GAP_FOR_THIS_ROLE (required, min 20 characters):
  - Must explain WHY this specific role wasn't a match — not a generic criticism
  - Bad: "insufficient experience"
  - Bad: "we found stronger candidates"
  - Good: "This role requires demonstrated experience leading distributed systems design
           at >100K daily users — the profile shows strong backend delivery but at
           smaller scale than this position requires"
  - Good: "The position needs someone who has owned the full product lifecycle from
           hypothesis to shipped feature — the profile shows strong delivery but evidence
           of discovery and prioritisation work is thin"

ENCOURAGEMENT (optional — ONLY set when gap is genuinely closable):
  - If the gap is: missing certification, insufficient seniority but strong trajectory,
    one missing technology → encouragement IS appropriate
  - If the gap is: fundamental domain mismatch, 5+ years short of requirement,
    critical contradiction → encouragement IS NOT appropriate (set to null)
  - If provided, make it CONCRETE and ACTIONABLE — what specific step would close the gap?

VERDICT CONTEXT:
  For STRONG_YES / YES: Tone should be warm and confirmatory — they passed
  For AMBIGUOUS / ESCALATE: Acknowledge uncertainty, keep tone professional
  For NO / STRONG_NO: Be honest but respectful — one strength, one gap, done

PRIVACY: Do not reproduce raw CV text verbatim. Reference the evidence by paraphrase.
Do not mention internal codes (STRONG_NO, tier levels, etc.) — write for the candidate.

Output a complete CandidateFeedback object."""

# ── LLM Setup ──────────────────────────────────────────────────────────────────
_llm = ChatGoogleGenerativeAI(
    model=settings.gemini_model_tier1,  # Flash — feedback doesn't need Pro reasoning
    google_api_key=settings.gemini_api_key,
    temperature=settings.llm_temperature,
)
_structured_llm = _llm.with_structured_output(CandidateFeedback)


@retry(
    stop=stop_after_attempt(settings.llm_max_retries),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _call_candidate_feedback_llm(
    candidate_id: str,
    verdict: str,
    evidence_snapshot: str,
    gap_signals: str,
    role_seniority: str,
    role_type: str,
) -> CandidateFeedback:
    """
    WHY: Isolated retry-wrapped LLM call. We pass evidence and gap signals
    rather than raw profile text so the feedback is grounded in evidence
    quality — the same evidence the decision was based on.
    """
    messages = [
        SystemMessage(content=CANDIDATE_FEEDBACK_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"CANDIDATE ID: {candidate_id}\n"
                f"VERDICT: {verdict}\n"
                f"ROLE SENIORITY: {role_seniority}\n"
                f"ROLE TYPE: {role_type}\n\n"
                f"--- EVIDENCE SNAPSHOT (top claims) ---\n{evidence_snapshot}\n\n"
                f"--- GAP SIGNALS (from fit analysis) ---\n{gap_signals}\n\n"
                f"Generate honest, respectful CandidateFeedback."
            )
        ),
    ]
    result: CandidateFeedback = _structured_llm.invoke(messages)
    return result


def _render_evidence_snapshot(evidence_bundle: Any) -> str:
    """
    WHY: The feedback LLM needs to know what POSITIVE evidence exists
    (to write the genuine_strength) and what gaps were found (for the gap message).

    HOW: Top 5 claims by weight + any silence flags.
    """
    lines = ["TOP EVIDENCE CLAIMS (by weight):"]
    sorted_claims = sorted(
        evidence_bundle.claims,
        key=lambda c: c.confidence_weight,
        reverse=True,
    )
    for claim in sorted_claims[:5]:
        lines.append(f"  [Tier {claim.tier}] {claim.text}")

    if evidence_bundle.builder_signals:
        lines.append(f"\nBUILDER SIGNALS: {'; '.join(evidence_bundle.builder_signals[:3])}")
    if evidence_bundle.maintainer_signals:
        lines.append(f"MAINTAINER SIGNALS: {'; '.join(evidence_bundle.maintainer_signals[:3])}")

    return "\n".join(lines)


def _render_gap_signals(fit_analysis: Any, decision: Any) -> str:
    """
    WHY: Gap signals tell the feedback LLM exactly what was missing — so it can
    write a specific, honest gap message instead of a generic one.
    """
    lines = []

    if fit_analysis.role_specific_red_flags:
        lines.append("ROLE-SPECIFIC RED FLAGS:")
        for flag in fit_analysis.role_specific_red_flags[:3]:
            lines.append(f"  - {flag}")

    if fit_analysis.probe_points:
        lines.append("\nPROBE POINTS (gaps to investigate):")
        for point in fit_analysis.probe_points[:3]:
            lines.append(f"  - {point}")

    if fit_analysis.learning_velocity_evidence.stagnation_flags:
        lines.append("\nSTAGNATION FLAGS:")
        for flag in fit_analysis.learning_velocity_evidence.stagnation_flags:
            lines.append(f"  - {flag}")

    lines.append(f"\nOVERALL CONFIDENCE: {decision.confidence_pct}%")
    lines.append(f"COMPOSITE FIT SCORE: {fit_analysis.composite_fit_score:.2f}")

    if fit_analysis.role_specific_green_flags:
        lines.append("\nGREEN FLAGS (genuine positives):")
        for flag in fit_analysis.role_specific_green_flags[:2]:
            lines.append(f"  - {flag}")

    return "\n".join(lines)


def candidate_feedback_node(state: ScreeningState) -> dict[str, Any]:
    """
    WHY: Generates personalised, evidence-grounded feedback for the candidate.
    Runs on ALL verdict paths — even STRONG_NO hard rejects generate feedback
    (though hard rejects may have already set candidate_feedback in tier1_prefilter).

    HOW:
    1. Check if candidate_feedback already set (hard reject path) — skip if so
    2. Validate state has decision, evidence_bundle, fit_analysis
    3. Call Gemini Flash to generate CandidateFeedback
    4. Return feedback and trajectory entry

    DESIGN: If candidate_feedback is already populated (by tier1_prefilter for hard
    rejects), we don't overwrite it. This saves an LLM call and respects the
    principle that tier1 feedback is appropriate for tier1 rejects.
    """
    node_name = "candidate_feedback"
    start_ms = time.time() * 1000

    # Skip if feedback already set (hard reject path)
    if state.get("candidate_feedback") is not None:
        trajectory_entry = make_trajectory_entry(
            node=node_name,
            start_time_ms=start_ms,
            reasoning_summary=(
                "Candidate feedback already generated by tier1_prefilter "
                "(hard reject). Skipping LLM call."
            ),
            output_summary="Skipped — feedback already present",
            model_used=None,
            cost_usd=0.0,
        )
        return {
            "trajectory": [trajectory_entry],
            "total_cost_usd": 0.0,
        }

    decision = state.get("decision")
    if decision is None:
        raise StateTransitionError(node_name, "decision")

    evidence_bundle = state.get("evidence_bundle")
    if evidence_bundle is None:
        raise StateTransitionError(node_name, "evidence_bundle")

    fit_analysis = state.get("fit_analysis")
    if fit_analysis is None:
        raise StateTransitionError(node_name, "fit_analysis")

    screening_input = state.get("screening_input")
    if screening_input is None:
        raise StateTransitionError(node_name, "screening_input")

    candidate_id = screening_input.candidate_id

    logger.info(
        "candidate_feedback started",
        node=node_name,
        candidate_id=candidate_id,
        verdict=decision.verdict,
    )

    evidence_snapshot = _render_evidence_snapshot(evidence_bundle)
    gap_signals = _render_gap_signals(fit_analysis, decision)

    try:
        candidate_feedback = _call_candidate_feedback_llm(
            candidate_id=candidate_id,
            verdict=decision.verdict,
            evidence_snapshot=evidence_snapshot,
            gap_signals=gap_signals,
            role_seniority=screening_input.role_seniority,
            role_type=screening_input.role_type,
        )
    except Exception as exc:
        raise LLMCallError(node_name, str(exc)) from exc

    prompt_token_estimate = (len(evidence_snapshot) + len(gap_signals)) // 4
    completion_token_estimate = 250
    cost_usd = estimate_token_cost(
        prompt_tokens=prompt_token_estimate,
        completion_tokens=completion_token_estimate,
        model_tier=1,  # Flash
    )

    has_encouragement = candidate_feedback.encouragement is not None

    trajectory_entry = make_trajectory_entry(
        node=node_name,
        start_time_ms=start_ms,
        reasoning_summary=(
            f"Candidate feedback generated for verdict: {decision.verdict}. "
            f"Genuine strength identified. "
            f"Role-specific gap articulated. "
            f"Encouragement included: {has_encouragement}."
        ),
        output_summary=(
            f"Feedback generated | verdict: {decision.verdict} | "
            f"encouragement: {has_encouragement}"
        ),
        evidence_keys=["feedback:genuine_strength", "feedback:gap_for_this_role"],
        model_used=settings.gemini_model_tier1,
        cost_usd=cost_usd,
    )

    logger.info(
        "candidate_feedback complete",
        node=node_name,
        candidate_id=candidate_id,
        verdict=decision.verdict,
        has_encouragement=has_encouragement,
        duration_ms=trajectory_entry.duration_ms,
        cost_usd=cost_usd,
    )

    return {
        "candidate_feedback": candidate_feedback,
        "trajectory": [trajectory_entry],
        "total_cost_usd": cost_usd,
    }
