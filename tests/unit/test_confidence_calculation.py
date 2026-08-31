"""
WHY: The confidence % is what all downstream decisions are built on.
The formula must be deterministic and correct — the same inputs always
produce the same output, regardless of when or how many times it runs.

HOW: The confidence formula is a 60/40 blend of evidence quality and fit:
  confidence = (evidence_score * 0.60 + fit_score * 0.40) * 100
  clamped to [0.0, 100.0]

Where:
  evidence_score = (total_weighted_score - silence_penalty) / normaliser
  fit_score      = FitAnalysis.composite_fit_score  (already 0.0–1.0)

Because the make_decision node is not yet implemented as a standalone node,
we test the formula directly as a pure function defined in this module.
This ensures the formula contract is locked down before the node is built.
"""

import pytest

from screen.schemas.analysis import FitAnalysis, LearningVelocityEvidence
from screen.schemas.evidence import Claim, EvidenceBundle, SIGNAL_WEIGHTS, SilenceFlag


# ── Formula implementation (mirrors make_decision node logic) ─────────────────

def _calculate_confidence(
    evidence_bundle: EvidenceBundle,
    fit_analysis: FitAnalysis,
) -> float:
    """Mirrors make_decision_node confidence calculation exactly."""
    raw_score = evidence_bundle.total_weighted_score - evidence_bundle.silence_penalty
    num_claims = max(len(evidence_bundle.claims), 1)
    per_claim_score = raw_score / num_claims
    normalised = (per_claim_score + 1.5) / 2.5
    evidence_score = max(0.0, min(1.0, normalised))
    fit_score = fit_analysis.composite_fit_score
    return round((evidence_score * 0.6 + fit_score * 0.4) * 100, 1)


# ── Test Helpers ──────────────────────────────────────────────────────────────

def _make_claim(tier: str, text: str = "test") -> Claim:
    return Claim(
        text=text,
        tier=tier,  # type: ignore[arg-type]
        confidence_weight=SIGNAL_WEIGHTS[tier],
        source_location=f"Test — tier {tier}",
        is_verifiable_externally=(tier == "A"),
    )


def _make_bundle(
    claims: list[Claim],
    silence_flags: list[SilenceFlag] | None = None,
    has_critical: bool = False,
) -> EvidenceBundle:
    return EvidenceBundle(
        candidate_id="test",
        claims=claims,
        silence_flags=silence_flags or [],
        has_critical_contradiction=has_critical,
    )


def _make_fit(
    technical: float = 0.5,
    experience: float = 0.5,
    learning: float = 0.5,
    builder: float = 0.5,
) -> FitAnalysis:
    return FitAnalysis(
        candidate_id="test",
        technical_fit=technical,
        technical_fit_rationale="test rationale",
        experience_level_fit=experience,
        experience_level_rationale="test rationale",
        learning_velocity_score=learning,
        learning_velocity_rationale="test rationale",
        learning_velocity_evidence=LearningVelocityEvidence(),
        builder_maintainer_score=builder,
        career_shape="ascending",
        career_velocity="steady",
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestConfidenceFormula:
    """
    WHY: Every branch of the confidence formula must be exercised to prove
    it handles extremes, common cases, and edge cases identically.
    """

    def test_high_evidence_quality_and_high_fit_produces_high_confidence(self) -> None:
        """
        Four Tier-A claims: raw=4.0, per_claim=1.0, normalised=1.0, evidence_score=1.0.
        Fit ≈ 0.86. confidence = (1.0*0.6 + 0.86*0.4)*100 ≈ 94.4% — well above 65%.
        """
        bundle = _make_bundle(claims=[
            _make_claim("A"),
            _make_claim("A"),
            _make_claim("A"),
            _make_claim("A"),
        ])
        fit = _make_fit(technical=0.9, experience=0.85, learning=0.85, builder=0.8)
        confidence = _calculate_confidence(bundle, fit)
        assert confidence >= 65.0, f"Expected ≥65%, got {confidence}%"

    def test_critical_contradiction_tanks_confidence_below_escalation_threshold(self) -> None:
        """
        A bundle with one positive A-claim and one D-claim (net score 1.0-1.5=-0.5)
        plus mediocre fit should produce low confidence below 45%.
        raw=-0.5, num_claims=2, per_claim=-0.25, normalised=(-0.25+1.5)/2.5=0.5,
        evidence_score=0.5. fit=0.3. confidence=(0.5*0.6+0.3*0.4)*100=42.0%.
        """
        bundle = _make_bundle(
            claims=[_make_claim("A"), _make_claim("D")],
            has_critical=True,
        )
        fit = _make_fit(technical=0.3, experience=0.3, learning=0.3, builder=0.3)
        confidence = _calculate_confidence(bundle, fit)
        assert confidence < 45.0, f"Expected <45%, got {confidence}%"

    def test_many_vague_claims_do_not_produce_high_confidence(self) -> None:
        """
        Ten Tier-C claims (score 3.0) with mediocre fit must not exceed STRONG_YES
        threshold (80%). Quantity of vague claims must not substitute for quality.
        raw=3.0, per_claim=0.3, normalised=(0.3+1.5)/2.5=0.72, evidence=0.72.
        fit=0.5. confidence=(0.72*0.6+0.5*0.4)*100=63.2%.
        """
        bundle = _make_bundle(claims=[_make_claim("C") for _ in range(10)])
        fit = _make_fit(technical=0.5, experience=0.5, learning=0.5, builder=0.5)
        confidence = _calculate_confidence(bundle, fit)
        assert confidence < 80.0, f"Expected <80%, got {confidence}%"

    def test_single_verified_claim_outweighs_three_vague_claims(self) -> None:
        """
        One Tier-A claim (weight 1.0) must produce a higher evidence score
        than three Tier-C claims (3 × 0.3 = 0.9). Quality beats quantity.
        """
        bundle_a = _make_bundle(claims=[_make_claim("A")])
        bundle_c = _make_bundle(claims=[_make_claim("C"), _make_claim("C"), _make_claim("C")])
        fit = _make_fit()  # Same fit for both

        confidence_a = _calculate_confidence(bundle_a, fit)
        confidence_c = _calculate_confidence(bundle_c, fit)

        assert confidence_a > confidence_c, (
            f"Tier-A confidence ({confidence_a}%) should exceed "
            f"3×Tier-C confidence ({confidence_c}%)"
        )

    def test_multiple_silence_flags_reduce_confidence(self) -> None:
        """
        Adding high-severity silence flags to an otherwise identical bundle
        must produce lower confidence than the same bundle without flags.
        """
        claims = [_make_claim("B"), _make_claim("B")]
        fit = _make_fit()

        bundle_clean = _make_bundle(claims=claims)
        bundle_silenced = _make_bundle(
            claims=claims,
            silence_flags=[
                SilenceFlag(
                    expected_signal="quantified outcomes",
                    absence_interpretation="Expected for senior",
                    severity="high",
                ),
                SilenceFlag(
                    expected_signal="architectural ownership",
                    absence_interpretation="Expected for staff",
                    severity="high",
                ),
            ],
        )

        conf_clean = _calculate_confidence(bundle_clean, fit)
        conf_silenced = _calculate_confidence(bundle_silenced, fit)
        assert conf_silenced < conf_clean, (
            f"Silence-penalised confidence ({conf_silenced}%) should be less "
            f"than clean confidence ({conf_clean}%)"
        )

    def test_confidence_is_capped_at_100_pct(self) -> None:
        """
        Even with maximum possible evidence score (5 Tier-A claims, per_claim=1.0,
        evidence_score=1.0) and perfect fit (1.0 on all dimensions), confidence
        must not exceed 100%.
        """
        bundle = _make_bundle(claims=[_make_claim("A") for _ in range(5)])
        fit = _make_fit(technical=1.0, experience=1.0, learning=1.0, builder=1.0)
        confidence = _calculate_confidence(bundle, fit)
        assert confidence <= 100.0

    def test_confidence_is_floored_at_0_pct(self) -> None:
        """
        Extreme negative evidence (many Tier-D claims) with zero fit scores
        must floor at 0%, never going negative.
        raw=-15.0, per_claim=-1.5, normalised=0.0, evidence_score=0.0. fit=0.0.
        confidence=0.0.
        """
        bundle = _make_bundle(claims=[_make_claim("D") for _ in range(10)])
        fit = _make_fit(technical=0.0, experience=0.0, learning=0.0, builder=0.0)
        confidence = _calculate_confidence(bundle, fit)
        assert confidence >= 0.0
        assert confidence == 0.0

    def test_confidence_formula_is_60_40_blend_of_evidence_and_fit(self) -> None:
        """
        With 3 Tier-C claims: raw=0.9, per_claim=0.3, normalised=(0.3+1.5)/2.5=0.72,
        evidence_score=0.72. fit=0.5 (all dims at 0.5).
          confidence = (0.72 * 0.60 + 0.5 * 0.40) * 100 = (0.432 + 0.20) * 100 = 63.2%

        This test locks down the exact 60/40 blend ratio using the per-claim normalisation.
        """
        # 3 Tier-C claims: raw=0.9, per_claim=0.3, normalised=0.72
        bundle = _make_bundle(claims=[_make_claim("C"), _make_claim("C"), _make_claim("C")])
        # fit: 0.5*0.35 + 0.5*0.25 + 0.5*0.25 + 0.5*0.15 = 0.5 composite
        fit = _make_fit(technical=0.5, experience=0.5, learning=0.5, builder=0.5)

        confidence = _calculate_confidence(bundle, fit)

        # per_claim = 0.3, normalised = (0.3 + 1.5) / 2.5 = 0.72
        # confidence = (0.72 * 0.60 + 0.5 * 0.40) * 100 = 63.2
        expected = round((0.72 * 0.60 + 0.5 * 0.40) * 100, 1)
        assert confidence == pytest.approx(expected, abs=0.1)

    def test_formula_is_deterministic_same_inputs_same_output(self) -> None:
        """
        Calling the formula twice with identical inputs must produce
        identical outputs — no randomness, no state dependency.
        """
        bundle = _make_bundle(claims=[_make_claim("A"), _make_claim("B")])
        fit = _make_fit(technical=0.7, experience=0.6, learning=0.65, builder=0.5)

        result_1 = _calculate_confidence(bundle, fit)
        result_2 = _calculate_confidence(bundle, fit)
        assert result_1 == result_2
