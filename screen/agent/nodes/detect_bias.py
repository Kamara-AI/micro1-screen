"""
WHY: Node 5 — the adversarial auditor. This node is unique in the pipeline:
it doesn't analyse the candidate, it audits OUR OWN PRIOR REASONING for bias.

This is the key insight behind SCREEN's bias detection approach: we don't try
to audit the raw CV (which tells us nothing about our reasoning) — we ask the
LLM to review the FitAnalysis it (or an equivalent model) just produced and
flag the specific cognitive biases that could have contaminated it.

The six bias types we check for:
  1. University prestige bias — "Harvard graduate" scored higher without evidence
  2. Name/demographic bias — scoring shifted by inferred ethnicity, gender, or culture
  3. Employment gap bias — gaps treated as negative without specific evidence
  4. Overqualification reflex — high experience rejected without role-specific reasoning
  5. Affinity bias — scoring inflated by shared background with (assumed) hiring manager
  6. Recency bias — recent roles overweighted vs. earlier signal-rich roles

HOW: We pass the FitAnalysis WITH its rationale text to Gemini Pro and ask it to
act as a bias auditor. The key prompt engineering trick is that we ask it to look
for SPECIFIC LINGUISTIC PATTERNS that indicate bias in the rationale strings —
not just whether the scores seem fair in the abstract.

FitAnalysis is frozen (immutable Pydantic model), so we use .model_copy(update={})
to produce a new FitAnalysis with has_bias_flag=True and bias_flags populated.
"""

import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from screen.core.config import settings
from screen.core.exceptions import LLMCallError, StateTransitionError
from screen.core.logging_config import get_logger
from screen.core.trajectory import estimate_token_cost, make_trajectory_entry
from screen.schemas.analysis import FitAnalysis
from screen.schemas.state import ScreeningState

logger = get_logger(__name__)

# ── Bias audit output schema ───────────────────────────────────────────────────
# WHY: We need a small intermediate schema to capture the bias audit result
# before merging it back into the FitAnalysis. This keeps the node's logic clean.

class _BiasAuditResult(BaseModel):
    """Internal schema for the bias detection LLM output."""
    has_bias: bool
    bias_flags: list[str]
    audit_summary: str


# ── System prompt ──────────────────────────────────────────────────────────────
DETECT_BIAS_SYSTEM_PROMPT = """You are an AI bias auditor reviewing a fit analysis produced by a recruitment AI.

Your job is to identify specific cognitive biases in the analysis. You are NOT re-evaluating
the candidate — you are auditing the REASONING TEXT in the prior analysis for bias markers.

BIAS TYPES TO LOOK FOR:

1. UNIVERSITY PRESTIGE BIAS
   Red phrases: "top university", "prestigious institution", "ivy league", "elite school",
   "Russell Group", treating university name as a positive signal without linking it to
   demonstrated capability.
   Correct pattern: Education should only matter as evidence of specific skills — not prestige.

2. NAME/DEMOGRAPHIC BIAS
   Red pattern: Any score shift that correlates with inferred candidate ethnicity, gender,
   national origin, or other demographic factor that should not affect job performance.
   Look for: different standards applied to equivalent evidence based on assumed identity.

3. EMPLOYMENT GAP BIAS
   Red phrases: "unexplained gap is concerning", "extended period without work suggests",
   "gap in employment raises questions", treating gap presence alone as negative.
   Correct pattern: A gap is ONLY material if there's specific evidence it indicates
   a problem (e.g., documented performance issue) — mere existence of a gap is neutral.

4. OVERQUALIFICATION REFLEX
   Red pattern: Penalising strong experience WITHOUT a specific argument for why it
   creates a real problem for this role (overqualification alone is not a valid reason).
   Look for: "too senior", "might get bored", "likely to leave soon" without evidence.

5. AFFINITY BIAS
   Red pattern: Scores boosted for candidates who share background traits with a
   presumed evaluator persona — same industry background, same education type, etc.
   Look for: Praise that references familiarity rather than evidence.

6. RECENCY BIAS
   Red pattern: Older, signal-rich roles systematically underweighted vs. recent roles,
   OR recent experience alone driving a high score despite thin evidence quality.
   Look for: rationale that only references the most recent role and ignores historical pattern.

HOW TO AUDIT:
   - Read each rationale field in the FitAnalysis
   - Look for the linguistic patterns above
   - If you find a potential bias, generate a specific flag:
     "[BIAS TYPE] detected in [field_name]: [specific phrase that triggered it] — [why this is bias]"
   - Set has_bias=True ONLY if you find a SPECIFIC, CONCRETE instance — not just vague concern
   - If the analysis is clean (rationales cite evidence, not proxies), set has_bias=False

OUTPUT:
   has_bias: true/false
   bias_flags: list of specific flag strings (empty if has_bias=false)
   audit_summary: 1-2 sentences describing what you checked and what you found

IMPORTANT: Do not be overly sensitive. Flag actual bias instances, not theoretical possibilities.
A false positive bias flag is harmful — it triggers an unnecessary escalation."""

# ── LLM Setup ──────────────────────────────────────────────────────────────────
_llm = ChatGoogleGenerativeAI(
    model=settings.gemini_model_tier2,
    google_api_key=settings.gemini_api_key,
    temperature=settings.llm_temperature,
)
_structured_llm = _llm.with_structured_output(_BiasAuditResult)


@retry(
    stop=stop_after_attempt(settings.llm_max_retries),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _call_detect_bias_llm(fit_analysis_text: str) -> _BiasAuditResult:
    """
    WHY: Isolated retry-wrapped LLM call. We pass the full FitAnalysis as structured
    text so the auditor can read every rationale field independently.

    HOW: The bias auditor sees the FitAnalysis rationale text but NOT the raw CV
    or candidate profile — this prevents it from doing its own assessment (which
    would defeat the purpose of auditing the prior reasoning).
    """
    messages = [
        SystemMessage(content=DETECT_BIAS_SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Audit the following FitAnalysis for cognitive bias in the reasoning:\n\n"
                f"{fit_analysis_text}"
            )
        ),
    ]
    result: _BiasAuditResult = _structured_llm.invoke(messages)
    return result


def _render_fit_analysis_for_audit(fit_analysis: FitAnalysis) -> str:
    """
    WHY: The bias auditor needs to see the reasoning TEXT — the rationale fields
    and the linguistic patterns in them. It doesn't need scores (numbers don't
    reveal bias patterns, words do).

    HOW: Produces a rationale-focused rendering of FitAnalysis. We include scores
    so the auditor can check if scores are consistent with stated rationale.
    """
    lines = [
        f"CANDIDATE: (anonymised)",
        f"CAREER SHAPE: {fit_analysis.career_shape}",
        f"CAREER VELOCITY: {fit_analysis.career_velocity}",
        "",
        f"TECHNICAL FIT: {fit_analysis.technical_fit:.2f}",
        f"  Rationale: {fit_analysis.technical_fit_rationale}",
        "",
        f"EXPERIENCE LEVEL FIT: {fit_analysis.experience_level_fit:.2f}",
        f"  Rationale: {fit_analysis.experience_level_rationale}",
        "",
        f"LEARNING VELOCITY: {fit_analysis.learning_velocity_score:.2f}",
        f"  Rationale: {fit_analysis.learning_velocity_rationale}",
        f"  New skills across roles: {', '.join(fit_analysis.learning_velocity_evidence.new_skills_across_roles) or 'none listed'}",
        f"  Self-directed signals: {', '.join(fit_analysis.learning_velocity_evidence.self_directed_signals) or 'none listed'}",
        f"  Stagnation flags: {', '.join(fit_analysis.learning_velocity_evidence.stagnation_flags) or 'none'}",
        "",
        f"BUILDER/MAINTAINER SCORE: {fit_analysis.builder_maintainer_score:.2f}",
        "",
        "RED FLAGS:",
    ]

    for flag in fit_analysis.role_specific_red_flags:
        lines.append(f"  - {flag}")
    if not fit_analysis.role_specific_red_flags:
        lines.append("  (none)")

    lines.append("GREEN FLAGS:")
    for flag in fit_analysis.role_specific_green_flags:
        lines.append(f"  - {flag}")
    if not fit_analysis.role_specific_green_flags:
        lines.append("  (none)")

    lines.append("NON-OBVIOUS FIT SIGNALS:")
    for signal in fit_analysis.non_obvious_fit_signals:
        lines.append(f"  - {signal}")
    if not fit_analysis.non_obvious_fit_signals:
        lines.append("  (none)")

    lines.append("PROBE POINTS (gaps to investigate):")
    for point in fit_analysis.probe_points:
        lines.append(f"  - {point}")

    if fit_analysis.company_contexts:
        lines.append("")
        lines.append("COMPANY CONTEXTS:")
        for ctx in fit_analysis.company_contexts:
            lines.append(
                f"  {ctx.company_name}: size={ctx.estimated_size}, "
                f"stage={ctx.stage_at_join}, "
                f"scope_appropriate={ctx.role_scope_appropriate}"
            )

    return "\n".join(lines)


def detect_bias_node(state: ScreeningState) -> dict[str, Any]:
    """
    WHY: Audits the FitAnalysis produced by analyze_fit for cognitive bias.
    This is a self-audit step — the same model family that produced the analysis
    is asked to audit it. This works because bias detection requires different
    reasoning (pattern matching on language) than fit analysis (evidence evaluation).

    HOW:
    1. Render FitAnalysis as rationale-focused text (what the bias auditor needs)
    2. Call Gemini Pro to audit for specific bias patterns
    3. If bias detected: produce updated FitAnalysis with has_bias_flag=True and flags populated
    4. FitAnalysis is frozen — use model_copy(update={}) to produce the updated version

    NOTE: FitAnalysis is a frozen Pydantic model. We must use model_copy(update={})
    to produce a new instance with the bias flags — direct mutation will raise a ValidationError.
    """
    node_name = "detect_bias"
    start_ms = time.time() * 1000

    fit_analysis = state.get("fit_analysis")
    if fit_analysis is None:
        raise StateTransitionError(node_name, "fit_analysis")

    evidence_bundle = state.get("evidence_bundle")
    if evidence_bundle is None:
        raise StateTransitionError(node_name, "evidence_bundle")

    screening_input = state.get("screening_input")
    if screening_input is None:
        raise StateTransitionError(node_name, "screening_input")

    candidate_id = screening_input.candidate_id

    logger.info(
        "detect_bias started",
        node=node_name,
        candidate_id=candidate_id,
    )

    fit_analysis_text = _render_fit_analysis_for_audit(fit_analysis)

    try:
        audit_result = _call_detect_bias_llm(fit_analysis_text)
    except Exception as exc:
        raise LLMCallError(node_name, str(exc)) from exc

    # Estimate cost: audit text is shorter than full analysis prompts
    prompt_token_estimate = len(fit_analysis_text) // 4
    completion_token_estimate = 300
    cost_usd = estimate_token_cost(
        prompt_tokens=prompt_token_estimate,
        completion_tokens=completion_token_estimate,
        model_tier=2,
    )

    if audit_result.has_bias:
        # Produce an updated FitAnalysis with bias flags set
        # FitAnalysis is frozen — model_copy(update={}) is the correct pattern
        updated_fit_analysis = fit_analysis.model_copy(
            update={
                "has_bias_flag": True,
                "bias_flags": audit_result.bias_flags,
            }
        )
        output_fit_analysis = updated_fit_analysis
        bias_summary = f"BIAS DETECTED — {len(audit_result.bias_flags)} flag(s)"
    else:
        output_fit_analysis = fit_analysis
        bias_summary = "No bias detected"

    trajectory_entry = make_trajectory_entry(
        node=node_name,
        start_time_ms=start_ms,
        reasoning_summary=(
            f"Bias audit complete. "
            f"{audit_result.audit_summary} "
            f"Bias flags: {len(audit_result.bias_flags)}. "
            f"Result: {bias_summary}."
        ),
        output_summary=bias_summary,
        evidence_keys=[f"bias_flag:{i}" for i in range(len(audit_result.bias_flags))],
        model_used=settings.gemini_model_tier2,
        cost_usd=cost_usd,
    )

    logger.info(
        "detect_bias complete",
        node=node_name,
        candidate_id=candidate_id,
        has_bias_flag=audit_result.has_bias,
        num_bias_flags=len(audit_result.bias_flags),
        duration_ms=trajectory_entry.duration_ms,
        cost_usd=cost_usd,
    )

    return {
        "fit_analysis": output_fit_analysis,
        "trajectory": [trajectory_entry],
        "total_cost_usd": cost_usd,
    }
