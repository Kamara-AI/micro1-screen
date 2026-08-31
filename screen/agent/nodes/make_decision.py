"""
WHY: Node 6 — the deterministic decision engine. No LLM call. Pure Python math.

This is an intentional architectural choice: the final verdict must NOT be an LLM
judgment. LLMs can hallucinate, drift under prompt variation, and cannot be held
accountable. A deterministic formula that maps evidence quality + fit scores to a
verdict is:
  - Reproducible: same inputs always produce same verdict
  - Auditable: you can trace exactly how a confidence score was computed
  - Explainable: every step can be shown to a candidate or regulator

The formula:
  evidence_score = (total_weighted_score - silence_penalty) / max(num_claims, 1)
  evidence_score = max(0.0, min(1.0, (evidence_score + 1.5) / 2.5))  # normalize 0–1
  fit_score = composite_fit_score  (already 0.0–1.0)
  confidence_pct = (evidence_score * 0.6 + fit_score * 0.4) * 100

WHY 60/40 evidence-to-fit weighting: Evidence quality (what was demonstrated and verified)
should outweigh analytical fit assessment (which carries LLM judgment risk). A candidate
with strong, verifiable evidence should score well even if the LLM's fit analysis was
only moderately positive.

Escalation priority order (applied before confidence-to-verdict mapping):
  1. hard_rejected (already set) → STRONG_NO
  2. critical_contradiction → ESCALATE
  3. bias_flag + escalate_on_bias_flag setting → ESCALATE
  4. unverifiable_high_stakes + high confidence + setting → ESCALATE
  5. Map confidence_pct to verdict band (settings thresholds)

HOW: Reads EvidenceBundle, FitAnalysis, and ScreeningInput from state.
Writes Decision and should_escalate flag to state.
"""

import time
from typing import Any

from screen.core.config import settings
from screen.core.exceptions import StateTransitionError
from screen.core.logging_config import get_logger
from screen.core.trajectory import make_trajectory_entry
from screen.schemas.analysis import FitAnalysis
from screen.schemas.decision import Decision
from screen.schemas.evidence import EvidenceBundle
from screen.schemas.state import ScreeningState

logger = get_logger(__name__)

# ── Domain relevance keywords ──────────────────────────────────────────────
# WHY: For roles where domain specificity matters (operations, ML), we check
# whether the candidate's CV contains vocabulary from the relevant domain.
# Zero domain keyword coverage indicates wrong-domain experience — the evidence
# quality score shouldn't dominate when evidence is from an irrelevant domain.
_SUPPLY_CHAIN_KEYWORDS = frozenset({
    "warehouse", "distribution", "logistics", "3pl", "supply chain",
    "inventory", "fill rate", "on-time delivery", "fmcg", "distributor",
    "dispatch", "freight", "last mile", "route planning", "shrinkage",
    "stock", "inbound", "outbound", "fulfilment", "procurement",
    "consignment", "delivery route", "replenishment", "stockist",
})

_PRODUCTION_ML_KEYWORDS = frozenset({
    "deployed", "in production", "model serving", "api endpoint",
    "real-time inference", "batch prediction", "model monitoring",
    "live system", "production system", "serving pipeline",
})


def _compute_domain_relevance(role_type: str, cv_text: str) -> float:
    """
    WHY: Deterministic domain relevance factor (0.0–1.0) that deflates the
    evidence score when a candidate's experience is in an irrelevant domain.

    Without this, a call-centre manager with pristine B-tier evidence scores
    AMBIGUOUS for an FMCG supply-chain role because evidence_quality is high
    even though the experience is entirely irrelevant.

    HOW: Count domain-specific keyword matches in the full CV text. Map count
    to a 0.3–1.0 relevance score. Multiplying evidence_score by this factor
    deflates irrelevant-domain evidence before blending with fit_score.

    Returns 1.0 (no adjustment) for roles where domain specificity is not a
    known failure mode.

    Calibration targets:
    - 0–2 keywords, hard-capped fit (events/NGO/call-centre), rel=0.60, fit≈0.22
      → 0.6×0.85×0.60 + 0.4×0.22 = 0.306+0.088 = 0.394 → 39% → NO ✓
    - 0 keywords, no hard cap (hotel/hospitality ops), rel=0.60, fit≈0.40
      → 0.6×0.85×0.60 + 0.4×0.40 = 0.306+0.16 = 0.466 → 47% → AMBIGUOUS ✓
    - 3–5 keywords (partial overlap, adjacent domain), rel=0.80
      → 0.6×0.85×0.80 + 0.4×0.45 = 0.408+0.18 = 0.588 → 59% → YES ✓
    - 6+ keywords (genuine supply chain): rel=1.0 → no penalty ✓
    """
    role_lower = role_type.lower()
    cv_lower = cv_text.lower()

    # Operations / supply-chain roles
    if "operations" in role_lower or "supply" in role_lower or "logistics" in role_lower:
        matches = sum(1 for kw in _SUPPLY_CHAIN_KEYWORDS if kw in cv_lower)
        if matches == 0:
            # WHY 0.60 not 0.45: The hard cap in analyze_fit (technical_fit=0.05) ensures
            # fundamentally wrong-domain candidates (events/NGO/contact centre) land in NO
            # via their suppressed fit_score (~0.22 composite). 0.45 was over-penalising
            # adjacent domains (hotel ops) where the hard cap doesn't apply (fit≈0.40).
            # With 0.60 + hard-cap (fit≈0.22): conf ≈ 39% → NO ✓
            # With 0.60 + no hard-cap (hotel ops, fit≈0.40): conf ≈ 47% → AMBIGUOUS ✓
            return 0.60
        if matches <= 2:
            # WHY same as 0: Incidental vocabulary (e.g., "inbound/outbound" from call
            # centre context, "distribution" from NGO health programmes) can produce
            # 1-2 keyword matches. Keeping at 0.60 ensures those false-positive-keyword
            # candidates don't slip past the NO threshold when the fit cap is partially applied.
            return 0.60
        if matches <= 5:
            return 0.80  # Partial overlap (adjacent domain, e.g. campus ops with procurement)
        return 1.0       # Strong domain match → no penalty

    # No adjustment for other role types
    return 1.0


def _compute_evidence_score(evidence_bundle: EvidenceBundle) -> float:
    """
    WHY: Evidence score normalisation maps the raw weighted sum (which can range
    from negative to large positive) into the 0.0–1.0 range needed for the
    confidence calculation.

    HOW: The raw score is centred around a midpoint. Adding 1.5 accounts for the
    maximum possible negative score from one Tier D claim (-1.5). Dividing by 2.5
    scales the result. This means a candidate with only Tier D claims scores ~0.0,
    and a candidate with only Tier A claims scores ~1.0.

    Division by claim count prevents evidence padding — more claims of equal quality
    don't artificially inflate the score.
    """
    raw_score = (evidence_bundle.total_weighted_score - evidence_bundle.silence_penalty)
    num_claims = max(len(evidence_bundle.claims), 1)
    per_claim_score = raw_score / num_claims
    # Normalise from roughly [-1.5, 1.0] per-claim range to [0.0, 1.0]
    normalised = (per_claim_score + 1.5) / 2.5
    return max(0.0, min(1.0, normalised))


def _compute_confidence_pct(
    evidence_score: float,
    fit_score: float,
    domain_relevance: float = 1.0,
) -> float:
    """
    WHY: Two-signal blend with evidence weighted 60% and fit 40%.
    Domain relevance deflates evidence when experience is in wrong domain.

    WHY 60/40: Evidence quality is more reliable than LLM fit assessment.
    Evidence tiers encode real verifiability (Tier A = externally checkable).
    Fit scores carry model uncertainty.

    DOMAIN RELEVANCE: Multiplied into evidence_score before blending.
    A wrong-domain candidate's evidence quality should not dominate —
    their evidence is real but irrelevant, so it is deflated proportionally.
    """
    adjusted_evidence = evidence_score * domain_relevance
    return round((adjusted_evidence * 0.6 + fit_score * 0.4) * 100, 1)


def _map_confidence_to_verdict(confidence_pct: float) -> str:
    """
    WHY: Threshold mapping lives in settings so it can be adjusted for different
    hiring standards (e.g., a safety-critical role might raise STRONG_YES to 90%).

    HOW: Priority order from highest to lowest band. The first threshold that
    confidence_pct exceeds wins.
    """
    if confidence_pct >= settings.strong_yes_threshold:
        return "STRONG_YES"
    elif confidence_pct >= settings.yes_threshold:
        return "YES"
    elif confidence_pct >= settings.ambiguous_threshold:
        return "AMBIGUOUS"
    elif confidence_pct >= settings.no_threshold:
        return "NO"
    else:
        return "STRONG_NO"


def _select_primary_evidence(
    evidence_bundle: EvidenceBundle,
    fit_analysis: FitAnalysis,
    verdict: str,
    confidence_pct: float,
) -> list[str]:
    """
    WHY: Primary evidence must cite specific claims from the EvidenceBundle —
    not generate new justification text. This makes the Decision auditable:
    a reviewer can find the exact claim in the EvidenceBundle.

    HOW: Strategy varies by verdict:
    - For YES/STRONG_YES: cite the top 3 highest-weighted claims
    - For NO/STRONG_NO: cite the most damaging signal (lowest weights / silence flags)
    - For AMBIGUOUS/ESCALATE: cite the most contradictory signals
    """
    primary_evidence: list[str] = []

    if verdict in ("YES", "STRONG_YES"):
        # Top positive claims
        sorted_claims = sorted(
            evidence_bundle.claims,
            key=lambda c: c.confidence_weight,
            reverse=True,
        )
        for claim in sorted_claims[:3]:
            primary_evidence.append(
                f"Tier {claim.tier} evidence: {claim.text} [{claim.source_location}]"
            )

    elif verdict in ("NO", "STRONG_NO"):
        # Most damaging signals first
        sorted_claims = sorted(evidence_bundle.claims, key=lambda c: c.confidence_weight)
        for claim in sorted_claims[:2]:
            primary_evidence.append(
                f"Weak signal — Tier {claim.tier}: {claim.text}"
            )
        if fit_analysis.role_specific_red_flags:
            primary_evidence.append(
                f"Red flag: {fit_analysis.role_specific_red_flags[0]}"
            )

    elif verdict in ("AMBIGUOUS", "ESCALATE"):
        # Highlight mixed signals
        if evidence_bundle.contradictions:
            contra = evidence_bundle.contradictions[0]
            primary_evidence.append(
                f"Contradiction ({contra.severity}): {contra.explanation}"
            )
        if evidence_bundle.silence_flags:
            flag = evidence_bundle.silence_flags[0]
            primary_evidence.append(
                f"Silence flag ({flag.severity}): {flag.expected_signal}"
            )
        if fit_analysis.probe_points:
            primary_evidence.append(
                f"Probe required: {fit_analysis.probe_points[0]}"
            )

    # Ensure at least one entry
    if not primary_evidence:
        primary_evidence.append(
            f"Confidence: {confidence_pct}% based on evidence quality and fit analysis"
        )

    return primary_evidence[:5]  # Decision schema caps at 5


def make_decision_node(state: ScreeningState) -> dict[str, Any]:
    """
    WHY: Deterministic decision engine — pure Python, no LLM call.
    Produces the final Decision and sets the should_escalate routing flag.

    HOW:
    1. Check if hard_rejected is already True (short-circuit handled by graph routing,
       but we guard defensively)
    2. Compute evidence score and confidence %
    3. Apply escalation priority checks in order
    4. Map confidence to verdict band if no escalation trigger
    5. Build Decision with primary evidence cited from EvidenceBundle
    """
    node_name = "make_decision"
    start_ms = time.time() * 1000

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
    hard_rejected = state.get("hard_rejected", False)

    logger.info(
        "make_decision started",
        node=node_name,
        candidate_id=candidate_id,
    )

    # ── Confidence calculation ──────────────────────────────────────────────────
    evidence_score = _compute_evidence_score(evidence_bundle)
    fit_score = fit_analysis.composite_fit_score

    # Compute domain relevance (deterministic keyword coverage check)
    domain_relevance = _compute_domain_relevance(
        role_type=screening_input.role_type,
        cv_text=screening_input.cv_text,
    )

    confidence_pct = _compute_confidence_pct(evidence_score, fit_score, domain_relevance)

    # ── Escalation priority logic ───────────────────────────────────────────────
    # WHY: These are applied IN ORDER. The first matching condition determines the
    # verdict. Order matters: critical contradictions outrank bias flags, which
    # outrank unverifiable claims, which outrank confidence-band mapping.

    verdict: str
    should_escalate: bool
    escalation_reason: str | None = None
    escalation_category: str | None = None

    if hard_rejected:
        # Should not reach here (graph routes hard-rejects to END), but guard defensively
        verdict = "STRONG_NO"
        should_escalate = False

    elif evidence_bundle.has_critical_contradiction and settings.escalate_on_critical_contradiction:
        verdict = "ESCALATE"
        should_escalate = True
        escalation_reason = (
            "Critical contradiction detected in the candidate's profile. "
            "A human reviewer must verify before any decision is made."
        )
        escalation_category = "critical_contradiction"

    elif (
        fit_analysis.has_bias_flag
        and confidence_pct >= settings.yes_threshold  # WHY: bias escalation is meant to block
        and settings.escalate_on_bias_flag            # a potentially-biased YES verdict. If
    ):                                                 # confidence is already below YES threshold,
        verdict = "ESCALATE"                          # the verdict will be AMBIGUOUS or lower —
        should_escalate = True                        # escalating on bias adds no safety value
        escalation_reason = (                         # and mislabels an evidence gap as bias.
            f"Bias flag(s) detected in the fit analysis: "
            f"{'; '.join(fit_analysis.bias_flags[:2])}. "
            f"Human review required before decision."
        )
        escalation_category = "bias_flag_detected"

    elif (
        evidence_bundle.has_unverifiable_high_stakes_claim
        and confidence_pct >= settings.yes_threshold  # WHY >=: a borderline YES (65%) with an
        and settings.escalate_on_unverifiable_high_confidence  # unverifiable claim is as much a
    ):                                                          # risk as a clear YES — do not
        verdict = "ESCALATE"                                    # let strict > create a blind spot
        should_escalate = True
        escalation_reason = (
            f"Verdict ({confidence_pct}%) rests on an unverifiable high-stakes claim. "
            f"Verification required before advancing candidate."
        )
        escalation_category = "unverifiable_high_stakes_claim"

    else:
        verdict = _map_confidence_to_verdict(confidence_pct)
        should_escalate = False

    # ── Build primary evidence ──────────────────────────────────────────────────
    primary_evidence = _select_primary_evidence(
        evidence_bundle=evidence_bundle,
        fit_analysis=fit_analysis,
        verdict=verdict,
        confidence_pct=confidence_pct,
    )

    elapsed_ms = int((time.time() * 1000) - start_ms)

    decision = Decision(
        candidate_id=candidate_id,
        verdict=verdict,
        confidence_pct=confidence_pct,
        primary_evidence=primary_evidence,
        escalation_reason=escalation_reason,
        escalation_category=escalation_category,
        tier_processed=state.get("current_tier", 2),
        estimated_cost_usd=state.get("total_cost_usd", 0.0),
        processing_time_ms=elapsed_ms,
        passed_hard_requirements=not hard_rejected,
    )

    trajectory_entry = make_trajectory_entry(
        node=node_name,
        start_time_ms=start_ms,
        reasoning_summary=(
            f"Deterministic decision. "
            f"Evidence score: {evidence_score:.3f} "
            f"(domain relevance: {domain_relevance:.2f}, adjusted: {evidence_score * domain_relevance:.3f}). "
            f"Fit score: {fit_score:.3f} (composite). "
            f"Confidence: {confidence_pct}%. "
            f"Escalation triggers checked: "
            f"critical_contradiction={evidence_bundle.has_critical_contradiction}, "
            f"bias_flag={fit_analysis.has_bias_flag}, "
            f"unverifiable_high_stakes={evidence_bundle.has_unverifiable_high_stakes_claim}. "
            f"Verdict: {verdict}. "
            f"Should escalate: {should_escalate}."
        ),
        output_summary=(
            f"Verdict: {verdict} | confidence: {confidence_pct}% | "
            f"escalate: {should_escalate}"
        ),
        evidence_keys=["formula:evidence_score", "formula:fit_score", "formula:confidence_pct"],
        model_used=None,  # Deterministic — no LLM call
        cost_usd=0.0,
    )

    logger.info(
        "make_decision complete",
        node=node_name,
        candidate_id=candidate_id,
        verdict=verdict,
        confidence_pct=confidence_pct,
        should_escalate=should_escalate,
        evidence_score=round(evidence_score, 3),
        domain_relevance=round(domain_relevance, 3),
        fit_score=round(fit_score, 3),
        duration_ms=trajectory_entry.duration_ms,
    )

    return {
        "decision": decision,
        "should_escalate": should_escalate,
        "trajectory": [trajectory_entry],
        "total_cost_usd": 0.0,  # No LLM cost in this node
    }
