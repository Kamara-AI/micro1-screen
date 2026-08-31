"""
WHY: The verdict routing is the most critical logic in SCREEN. A wrong routing
(escalating a clear YES or passing a fraudulent candidate) undermines everything.
Every branch of the routing logic must be tested.

HOW: The routing logic is a priority-ordered decision tree:
  1. hard_rejected → STRONG_NO (highest priority, overrides all)
  2. has_critical_contradiction → ESCALATE (if escalation enabled)
  3. has_bias_flag → ESCALATE (if escalation enabled)
  4. has_unverifiable_high_stakes_claim + high confidence → ESCALATE
  5. confidence >= 80 → STRONG_YES
  6. confidence >= 65 → YES
  7. confidence >= 45 → AMBIGUOUS
  8. confidence >= 25 → NO
  9. confidence < 25  → STRONG_NO

We implement and test this routing function directly so the logic is testable
without LangGraph state machinery.
"""

from typing import Literal

import pytest

from screen.schemas.evidence import EvidenceBundle, Claim, SIGNAL_WEIGHTS

# ── Routing function (mirrors make_decision node logic) ───────────────────────
# WHY: Implementing the routing as a pure function here allows exhaustive
# testing of every branch. The make_decision node will call this exact logic.

Verdict = Literal["STRONG_YES", "YES", "AMBIGUOUS", "NO", "STRONG_NO", "ESCALATE"]


def _determine_verdict(
    confidence_pct: float,
    hard_rejected: bool,
    has_critical_contradiction: bool,
    has_bias_flag: bool,
    has_unverifiable_high_stakes_claim: bool,
    escalate_on_critical_contradiction: bool = True,
    escalate_on_bias_flag: bool = True,
    escalate_on_unverifiable_high_confidence: bool = True,
    strong_yes_threshold: float = 80.0,
    yes_threshold: float = 65.0,
    ambiguous_threshold: float = 45.0,
    no_threshold: float = 25.0,
) -> Verdict:
    """
    WHY: Pure routing function that encodes the priority-ordered verdict logic.
    Priority order matters — a hard-rejected candidate must NEVER be ESCALATED,
    even if they also have a critical contradiction.

    HOW: Each condition is checked in priority order. First match wins.

    Args:
        confidence_pct: The calculated confidence percentage [0, 100].
        hard_rejected:  True if candidate failed a hard requirement.
        has_critical_contradiction: True if EvidenceBundle has critical contradiction.
        has_bias_flag:  True if FitAnalysis.has_bias_flag is True.
        has_unverifiable_high_stakes_claim: True if high-impact claim cannot be verified.
        escalate_on_critical_contradiction: Settings flag.
        escalate_on_bias_flag: Settings flag.
        escalate_on_unverifiable_high_confidence: Settings flag.
        strong_yes_threshold: % floor for STRONG_YES.
        yes_threshold: % floor for YES.
        ambiguous_threshold: % floor for AMBIGUOUS.
        no_threshold: % floor for NO.

    Returns:
        One of the six verdict strings.
    """
    # Priority 1: Hard rejection always wins
    if hard_rejected:
        return "STRONG_NO"

    # Priority 2: Critical contradiction → mandatory ESCALATE
    if has_critical_contradiction and escalate_on_critical_contradiction:
        return "ESCALATE"

    # Priority 3: Bias flag → ESCALATE
    if has_bias_flag and escalate_on_bias_flag:
        return "ESCALATE"

    # Priority 4: Unverifiable high-stakes claim + high confidence → ESCALATE
    # WHY: High confidence with unverifiable evidence is dangerous — we'd be
    # confidently recommending based on claims we cannot check.
    if (
        has_unverifiable_high_stakes_claim
        and escalate_on_unverifiable_high_confidence
        and confidence_pct >= yes_threshold  # high confidence = yes_threshold or above
    ):
        return "ESCALATE"

    # Priority 5–9: Confidence-band routing
    if confidence_pct >= strong_yes_threshold:
        return "STRONG_YES"
    if confidence_pct >= yes_threshold:
        return "YES"
    if confidence_pct >= ambiguous_threshold:
        return "AMBIGUOUS"
    if confidence_pct >= no_threshold:
        return "NO"
    return "STRONG_NO"


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestHardRejectRouting:
    """
    WHY: Hard rejection is the highest-priority condition. It must override
    everything — even a candidate with 95% confidence who also failed a hard
    requirement must get STRONG_NO, not STRONG_YES or ESCALATE.
    """

    def test_hard_rejected_candidate_gets_strong_no_regardless_of_confidence(self) -> None:
        """A hard-rejected candidate routes to STRONG_NO even with 95% confidence."""
        verdict = _determine_verdict(
            confidence_pct=95.0,
            hard_rejected=True,
            has_critical_contradiction=False,
            has_bias_flag=False,
            has_unverifiable_high_stakes_claim=False,
        )
        assert verdict == "STRONG_NO"

    def test_hard_rejected_with_critical_contradiction_still_gets_strong_no(self) -> None:
        """Hard reject beats critical contradiction — STRONG_NO, not ESCALATE."""
        verdict = _determine_verdict(
            confidence_pct=50.0,
            hard_rejected=True,
            has_critical_contradiction=True,
            has_bias_flag=False,
            has_unverifiable_high_stakes_claim=False,
        )
        assert verdict == "STRONG_NO"


class TestEscalationRouting:
    """
    WHY: Escalation conditions are second in priority. They must trigger
    regardless of confidence level (within the escalation conditions themselves).
    """

    def test_critical_contradiction_always_escalates_regardless_of_confidence(self) -> None:
        """A critical contradiction routes to ESCALATE even with low confidence (30%)."""
        for confidence in [10.0, 30.0, 60.0, 85.0]:
            verdict = _determine_verdict(
                confidence_pct=confidence,
                hard_rejected=False,
                has_critical_contradiction=True,
                has_bias_flag=False,
                has_unverifiable_high_stakes_claim=False,
                escalate_on_critical_contradiction=True,
            )
            assert verdict == "ESCALATE", (
                f"Expected ESCALATE at {confidence}% confidence, got {verdict}"
            )

    def test_bias_flag_escalates_when_setting_is_true(self) -> None:
        """A bias flag routes to ESCALATE when escalate_on_bias_flag=True."""
        verdict = _determine_verdict(
            confidence_pct=70.0,
            hard_rejected=False,
            has_critical_contradiction=False,
            has_bias_flag=True,
            has_unverifiable_high_stakes_claim=False,
            escalate_on_bias_flag=True,
        )
        assert verdict == "ESCALATE"

    def test_bias_flag_does_not_escalate_when_setting_is_false(self) -> None:
        """When escalate_on_bias_flag=False, bias flag is noted but routing continues normally."""
        verdict = _determine_verdict(
            confidence_pct=70.0,
            hard_rejected=False,
            has_critical_contradiction=False,
            has_bias_flag=True,
            has_unverifiable_high_stakes_claim=False,
            escalate_on_bias_flag=False,
        )
        # Should fall through to confidence-band routing: 70% → YES
        assert verdict == "YES"

    def test_critical_contradiction_does_not_escalate_when_setting_is_false(self) -> None:
        """When escalate_on_critical_contradiction=False, falls through to confidence band."""
        verdict = _determine_verdict(
            confidence_pct=75.0,
            hard_rejected=False,
            has_critical_contradiction=True,
            has_bias_flag=False,
            has_unverifiable_high_stakes_claim=False,
            escalate_on_critical_contradiction=False,
        )
        assert verdict == "YES"

    def test_unverifiable_claim_with_high_confidence_escalates(self) -> None:
        """Unverifiable high-stakes claim combined with confidence ≥ yes_threshold → ESCALATE."""
        verdict = _determine_verdict(
            confidence_pct=72.0,
            hard_rejected=False,
            has_critical_contradiction=False,
            has_bias_flag=False,
            has_unverifiable_high_stakes_claim=True,
            escalate_on_unverifiable_high_confidence=True,
        )
        assert verdict == "ESCALATE"

    def test_unverifiable_claim_with_low_confidence_does_not_escalate(self) -> None:
        """
        Low confidence + unverifiable claim does NOT escalate.
        We only escalate when we would otherwise confidently recommend an unverifiable candidate.
        Low confidence → routing falls through to NO or STRONG_NO instead.
        """
        verdict = _determine_verdict(
            confidence_pct=30.0,
            hard_rejected=False,
            has_critical_contradiction=False,
            has_bias_flag=False,
            has_unverifiable_high_stakes_claim=True,
            escalate_on_unverifiable_high_confidence=True,
            yes_threshold=65.0,
        )
        # 30% < 65% (yes_threshold) → unverifiable escalation does not trigger
        # Falls through to NO (25 ≤ 30 < 45)
        assert verdict == "NO"


class TestConfidenceBandRouting:
    """
    WHY: The five confidence bands (STRONG_YES, YES, AMBIGUOUS, NO, STRONG_NO)
    must map to the correct thresholds. Off-by-one errors here would cause
    systematic misrouting of candidates near threshold boundaries.
    """

    def test_confidence_above_80_maps_to_strong_yes(self) -> None:
        """Confidence ≥ 80% → STRONG_YES."""
        for confidence in [80.0, 85.0, 95.0, 100.0]:
            verdict = _determine_verdict(
                confidence_pct=confidence,
                hard_rejected=False,
                has_critical_contradiction=False,
                has_bias_flag=False,
                has_unverifiable_high_stakes_claim=False,
            )
            assert verdict == "STRONG_YES", f"Expected STRONG_YES at {confidence}%, got {verdict}"

    def test_confidence_between_65_and_80_maps_to_yes(self) -> None:
        """65% ≤ confidence < 80% → YES."""
        for confidence in [65.0, 70.0, 75.0, 79.9]:
            verdict = _determine_verdict(
                confidence_pct=confidence,
                hard_rejected=False,
                has_critical_contradiction=False,
                has_bias_flag=False,
                has_unverifiable_high_stakes_claim=False,
            )
            assert verdict == "YES", f"Expected YES at {confidence}%, got {verdict}"

    def test_confidence_between_45_and_65_maps_to_ambiguous(self) -> None:
        """45% ≤ confidence < 65% → AMBIGUOUS."""
        for confidence in [45.0, 50.0, 55.0, 64.9]:
            verdict = _determine_verdict(
                confidence_pct=confidence,
                hard_rejected=False,
                has_critical_contradiction=False,
                has_bias_flag=False,
                has_unverifiable_high_stakes_claim=False,
            )
            assert verdict == "AMBIGUOUS", f"Expected AMBIGUOUS at {confidence}%, got {verdict}"

    def test_confidence_between_25_and_45_maps_to_no(self) -> None:
        """25% ≤ confidence < 45% → NO."""
        for confidence in [25.0, 30.0, 35.0, 44.9]:
            verdict = _determine_verdict(
                confidence_pct=confidence,
                hard_rejected=False,
                has_critical_contradiction=False,
                has_bias_flag=False,
                has_unverifiable_high_stakes_claim=False,
            )
            assert verdict == "NO", f"Expected NO at {confidence}%, got {verdict}"

    def test_confidence_below_25_maps_to_strong_no(self) -> None:
        """confidence < 25% → STRONG_NO."""
        for confidence in [0.0, 10.0, 20.0, 24.9]:
            verdict = _determine_verdict(
                confidence_pct=confidence,
                hard_rejected=False,
                has_critical_contradiction=False,
                has_bias_flag=False,
                has_unverifiable_high_stakes_claim=False,
            )
            assert verdict == "STRONG_NO", f"Expected STRONG_NO at {confidence}%, got {verdict}"

    def test_exactly_at_threshold_boundaries_routes_to_upper_band(self) -> None:
        """
        Exactly at a threshold (e.g., 65.0, 45.0, 25.0) routes to the upper band,
        not the lower one. Thresholds are inclusive lower bounds.
        """
        assert _determine_verdict(
            confidence_pct=65.0,
            hard_rejected=False,
            has_critical_contradiction=False,
            has_bias_flag=False,
            has_unverifiable_high_stakes_claim=False,
        ) == "YES"

        assert _determine_verdict(
            confidence_pct=45.0,
            hard_rejected=False,
            has_critical_contradiction=False,
            has_bias_flag=False,
            has_unverifiable_high_stakes_claim=False,
        ) == "AMBIGUOUS"

        assert _determine_verdict(
            confidence_pct=25.0,
            hard_rejected=False,
            has_critical_contradiction=False,
            has_bias_flag=False,
            has_unverifiable_high_stakes_claim=False,
        ) == "NO"
