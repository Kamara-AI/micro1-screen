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
from screen.core.domain_calibration import get_calibration
from screen.core.exceptions import StateTransitionError
from screen.core.logging_config import get_logger
from screen.core.trajectory import make_trajectory_entry
from screen.schemas.analysis import FitAnalysis
from screen.schemas.decision import Decision
from screen.schemas.evidence import EvidenceBundle
from screen.schemas.state import ScreeningState

logger = get_logger(__name__)

# ── Operations / supply-chain keyword gate ─────────────────────────────────
# WHY: Kept as a dedicated constant because the ops keyword gate predates the
# general quality-ratio approach and operates on a different signal (CV vocabulary
# coverage, not evidence-tier distribution). Removing it would break calibrated
# thresholds that were validated against known ops mis-match candidates.
_SUPPLY_CHAIN_KEYWORDS = frozenset({
    "warehouse", "distribution", "logistics", "3pl", "supply chain",
    "inventory", "fill rate", "on-time delivery", "fmcg", "distributor",
    "dispatch", "freight", "last mile", "route planning", "shrinkage",
    "stock", "inbound", "outbound", "fulfilment", "procurement",
    "consignment", "delivery route", "replenishment", "stockist",
})


def _compute_domain_relevance(
    role_type: str,
    cv_text: str,
    evidence_bundle: EvidenceBundle,
) -> tuple[float, float]:
    """
    WHY: Returns (evidence_relevance, fit_relevance) — two separate multipliers
    applied before the 60/40 blend. Splitting the signal lets us penalise
    evidence quality independently of the LLM's fit judgment.

    For ops/supply-chain: vocabulary coverage in the CV is the primary signal
    (proven approach, kept unchanged). fit_relevance stays 1.0 because the
    hard-cap in analyze_fit already suppresses fit_score for wrong-domain candidates.

    For all other domains: Tier A/B quality ratio in the evidence bundle is the
    primary signal. Pure Tier-C evidence (no verifiable or stated facts, only
    vague outcome language) indicates inflation without substance — the candidate
    is describing results without demonstrating how they were achieved.

    WHY quality ratio matters: The normalisation formula floors evidence_score at
    ~0.72 even for 10 pure Tier-C claims. Without a relevance penalty, a marketing
    candidate who writes "drove growth", "increased brand awareness", and "led
    campaigns" (all Tier C) scores evidence_score≈0.72, which blends to AMBIGUOUS
    when fit_score≈0.45. The quality-ratio penalty deflates both sides to land in NO.

    Calibration targets (non-ops, outcome-language domain e.g. Marketing):
    - quality_ratio=0.0, ev≈0.72, fit≈0.40 → ev_rel=0.62, fit_rel=0.82
      → 0.72×0.62×0.6 + 0.40×0.82×0.4 = 0.268+0.131 = 0.399 → 40% → NO ✓
    - quality_ratio=0.25, ev≈0.76, fit≈0.50 → ev_rel=0.85, fit_rel=0.92
      → 0.76×0.85×0.6 + 0.50×0.92×0.4 = 0.388+0.184 = 0.572 → 57% → AMBIGUOUS ✓
    - quality_ratio=0.55, ev≈0.85, fit≈0.70 → ev_rel=1.0, fit_rel=1.0
      → 0.85×0.6 + 0.70×0.4 = 0.510+0.280 = 0.790 → 79% → YES ✓

    Calibration targets (non-ops, technical domain e.g. SWE, DS/ML):
    - quality_ratio=0.0: ev_rel=0.55, fit_rel=0.75 (stronger — Tier A/B expected)
    """
    role_lower = role_type.lower()
    cv_lower = cv_text.lower()

    # ── Operations / supply-chain: keyword-coverage gate (preserved) ───────────
    if any(kw in role_lower for kw in ("operations", "supply", "logistics")):
        matches = sum(1 for kw in _SUPPLY_CHAIN_KEYWORDS if kw in cv_lower)
        if matches <= 2:
            # WHY 0.60: hard-cap in analyze_fit suppresses fit_score for truly
            # wrong-domain candidates (events/NGO → fit≈0.22 → conf≈39% → NO).
            # For adjacent domains without a hard cap (hotel ops → fit≈0.40),
            # 0.60 yields conf≈47% → AMBIGUOUS, which is the correct outcome.
            return (0.60, 1.0)
        if matches <= 5:
            return (0.80, 1.0)  # Partial overlap (adjacent domain)
        return (1.0, 1.0)       # Strong domain match → no penalty

    # ── All other domains: Tier A/B quality ratio ──────────────────────────────
    total_claims = len(evidence_bundle.claims)
    if total_claims == 0:
        return (1.0, 1.0)

    quality_claims = sum(1 for c in evidence_bundle.claims if c.tier in ("A", "B"))
    quality_ratio = quality_claims / total_claims

    # No penalty for candidates with substantial verifiable/stated evidence
    if quality_ratio >= 0.40:
        return (1.0, 1.0)

    # Mild penalty: some quality claims but outcome-language dominates
    if quality_ratio >= 0.20:
        return (0.85, 0.92)

    # Strong penalty: pure Tier-C (vague outcome language, no verifiable facts)
    # Calibration varies by domain type:
    # - Technical domains (SWE, ML, DevOps): stronger penalty because Tier A/B is
    #   always achievable (GitHub links, deployed models, uptime SLAs)
    # - Outcome domains (marketing, sales, HR): lighter penalty because some roles
    #   genuinely produce mostly outcome language — but still must penalise inflation
    calibration = get_calibration(role_type)
    if calibration.production_check_enabled:
        # Technical domain: Tier A/B should always be present — pure C is a red flag
        return (0.55, 0.75)
    else:
        # Outcome-language domain: penalise but less aggressively
        return (0.62, 0.82)


def _compute_evidence_score(evidence_bundle: EvidenceBundle) -> float:
    """
    WHY: Evidence score normalisation maps the raw weighted sum (which can range
    from negative to large positive) into the 0.0–1.0 range needed for the
    confidence calculation.

    HOW: The raw score is centred around a midpoint. Adding 1.5 accounts for the
    maximum possible negative score from one Tier D claim (-1.5). Dividing by 2.5
    scales the result.

    Per-tier per-claim scores under current weights:
      A (1.0)  → normalised = (1.0+1.5)/2.5 = 1.00  — verified evidence, full score
      B (0.7)  → normalised = (0.7+1.5)/2.5 = 0.88  — stated evidence, strong positive
      C (0.1)  → normalised = (0.1+1.5)/2.5 = 0.64  — vague evidence, minimal positive signal
      D (-1.5) → normalised = (-1.5+1.5)/2.5 = 0.00 — contradicted, floor

    WHY C=0.64 (below YES threshold): a candidate with only vague claims normalises to
    0.64, which combined with neutral fit (0.5) gives 58.4% confidence — below the YES
    threshold of 65%. Vague language cannot win a YES on its own. Previously, C=0.3
    placed pure-C evidence at 0.72 (63% confidence), too close to YES territory.
    C=0.0 was tested but catastrophically deflated legitimate strong candidates whose
    minor achievements were reclassified by the tighter Tier B definition. C=0.1 is
    the calibrated midpoint: discourages vague-claim inflation without destroying
    strong candidates who have a handful of single-element claims.

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
    evidence_relevance: float = 1.0,
    fit_relevance: float = 1.0,
) -> float:
    """
    WHY: Two-signal blend with evidence weighted 60% and fit 40%.
    Separate relevance multipliers allow evidence and fit to be deflated
    independently based on domain signal quality.

    WHY 60/40: Evidence quality is more reliable than LLM fit assessment.
    Evidence tiers encode real verifiability (Tier A = externally checkable).
    Fit scores carry model uncertainty.

    WHY SEPARATE MULTIPLIERS: For ops domain-mismatch, only evidence is
    deflated (fit already suppressed by hard-cap in analyze_fit). For
    outcome-language inflation (e.g. marketing with pure Tier-C claims),
    both are deflated because the LLM fit score can also be inflated by
    confident outcome language without real metrics.
    """
    adjusted_evidence = evidence_score * evidence_relevance
    adjusted_fit = fit_score * fit_relevance
    return round((adjusted_evidence * 0.6 + adjusted_fit * 0.4) * 100, 1)


def _map_confidence_to_verdict(
    confidence_pct: float,
    strong_yes_threshold: float | None = None,
    ambiguous_threshold: float | None = None,
) -> str:
    """
    WHY: Threshold mapping lives in settings so it can be adjusted for different
    hiring standards (e.g., a safety-critical role might raise STRONG_YES to 90%).
    Domain-specific overrides allow domains where evidence quality is structurally
    different (e.g. Digital Marketing, where Tier A evidence is rare) to use
    calibrated thresholds without touching the global setting.

    Domain-specific thresholds currently in use:
      - strong_yes_threshold: Digital Marketing uses 75 (vs global 86), because
        Tier A evidence (GitHub repos, public APIs) is structurally absent.
      - ambiguous_threshold: Digital Marketing uses 55 (vs global 45), because
        weak candidates who write generic outcome language cluster at 49-55%.

    HOW: Priority order from highest to lowest band. The first threshold that
    confidence_pct exceeds wins.
    """
    sy_threshold = strong_yes_threshold if strong_yes_threshold is not None else settings.strong_yes_threshold
    amb_threshold = ambiguous_threshold if ambiguous_threshold is not None else settings.ambiguous_threshold
    if confidence_pct >= sy_threshold:
        return "STRONG_YES"
    elif confidence_pct >= settings.yes_threshold:
        return "YES"
    elif confidence_pct >= amb_threshold:
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

    # Compute domain relevance (two-factor: evidence and fit, separately)
    # WHY: role_description provides the fine-grained domain title for calibration;
    # fall back to broad role_type if not set.
    domain_str = screening_input.role_description or screening_input.role_type
    domain_calibration = get_calibration(domain_str)
    evidence_relevance, fit_relevance = _compute_domain_relevance(
        role_type=domain_str,
        cv_text=screening_input.cv_text,
        evidence_bundle=evidence_bundle,
    )

    confidence_pct = _compute_confidence_pct(
        evidence_score, fit_score, evidence_relevance, fit_relevance
    )

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

    elif (
        evidence_bundle.builder_maintainer_verdict == "insufficient_data"
        and confidence_pct < settings.yes_threshold
    ):
        # WHY: A candidate whose CV provides insufficient evidence to classify as
        # builder or maintainer is by definition an unknown — the right verdict is
        # AMBIGUOUS (phone screen needed), not NO/STRONG_NO (rejection). Without
        # the phone screen, we cannot distinguish a genuine weak candidate from one
        # who simply writes very sparse CVs. The AMBIGUOUS verdict preserves
        # optionality; NO discards candidates who might be strong.
        # GATE: only applies below YES threshold — if confidence is already above
        # YES, the LLM found enough evidence to act, so no override is needed.
        verdict = "AMBIGUOUS"
        should_escalate = False

    else:
        verdict = _map_confidence_to_verdict(
            confidence_pct,
            strong_yes_threshold=domain_calibration.strong_yes_threshold,
            ambiguous_threshold=domain_calibration.ambiguous_threshold,
        )
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
            f"(ev_rel={evidence_relevance:.2f}, adjusted={evidence_score * evidence_relevance:.3f}). "
            f"Fit score: {fit_score:.3f} "
            f"(fit_rel={fit_relevance:.2f}, adjusted={fit_score * fit_relevance:.3f}). "
            f"Confidence: {confidence_pct}%. "
            f"STRONG_YES threshold: {domain_calibration.strong_yes_threshold}, "
            f"AMBIGUOUS threshold: {domain_calibration.ambiguous_threshold} "
            f"(domain: {domain_calibration.name}). "
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
        evidence_relevance=round(evidence_relevance, 2),
        fit_score=round(fit_score, 3),
        fit_relevance=round(fit_relevance, 2),
        duration_ms=trajectory_entry.duration_ms,
    )

    return {
        "decision": decision,
        "should_escalate": should_escalate,
        "trajectory": [trajectory_entry],
        "total_cost_usd": 0.0,  # No LLM cost in this node
    }
