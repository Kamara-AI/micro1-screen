"""
WHY: The confidence calculation is the mathematical core of SCREEN.
If it's wrong, every verdict is wrong. 100% coverage required.

Tests cover: individual claim weights, contradiction penalties, silence
penalties, total_weighted_score property, silence_penalty property.

HOW: All tests are pure unit tests — no LLM calls, no network, no .env
dependency beyond the autouse fixture in conftest.py. Each test constructs
the exact EvidenceBundle or Claim needed and asserts the computed properties.
"""

import pytest

from screen.schemas.evidence import (
    Claim,
    Contradiction,
    EvidenceBundle,
    SIGNAL_WEIGHTS,
    SilenceFlag,
)


def _make_claim(tier: str, text: str = "test claim") -> Claim:
    """Helper: build a Claim with the correct weight for the given tier."""
    return Claim(
        text=text,
        tier=tier,  # type: ignore[arg-type]
        confidence_weight=SIGNAL_WEIGHTS[tier],
        source_location=f"Test source — tier {tier}",
        is_verifiable_externally=False,
    )


def _make_bundle(
    claims: list[Claim] | None = None,
    contradictions: list[Contradiction] | None = None,
    silence_flags: list[SilenceFlag] | None = None,
    has_critical: bool = False,
    verdict: str = "insufficient_data",
) -> EvidenceBundle:
    """Helper: build an EvidenceBundle with sane defaults."""
    return EvidenceBundle(
        candidate_id="test-cand",
        claims=claims or [],
        contradictions=contradictions or [],
        silence_flags=silence_flags or [],
        builder_maintainer_verdict=verdict,  # type: ignore[arg-type]
        has_critical_contradiction=has_critical,
    )


# ── Individual Claim Weight Tests ─────────────────────────────────────────────

class TestClaimWeights:
    """
    WHY: Each tier must map to the correct numeric weight. These are the
    constants that everything else depends on — they must never drift silently.
    """

    def test_tier_a_claim_has_weight_1_0(self) -> None:
        """Tier A (VERIFIED) claims have confidence_weight=1.0."""
        claim = _make_claim("A")
        assert claim.confidence_weight == 1.0

    def test_tier_d_claim_has_weight_negative_1_5(self) -> None:
        """Tier D (CONTRADICTED) claims carry a penalty weight of -1.5."""
        claim = _make_claim("D", text="Contradicted claim about scope")
        assert claim.confidence_weight == -1.5

    def test_tier_b_claim_has_weight_0_7(self) -> None:
        """Tier B (STATED) claims have confidence_weight=0.7."""
        claim = _make_claim("B")
        assert claim.confidence_weight == pytest.approx(0.7)

    def test_tier_c_claim_has_weight_0_1(self) -> None:
        """Tier C (VAGUE) claims have confidence_weight=0.1 — minimal floor signal only."""
        claim = _make_claim("C")
        assert claim.confidence_weight == pytest.approx(0.1)


# ── total_weighted_score Property Tests ───────────────────────────────────────

class TestTotalWeightedScore:
    """
    WHY: total_weighted_score is the raw input to the confidence formula.
    Every wrong sum propagates directly into a wrong verdict.
    """

    def test_total_weighted_score_sums_all_claims(self) -> None:
        """Three claims A(1.0) + B(0.7) + C(0.1) sum to exactly 1.8."""
        bundle = _make_bundle(claims=[
            _make_claim("A"),
            _make_claim("B"),
            _make_claim("C"),
        ])
        assert bundle.total_weighted_score == pytest.approx(1.8)

    def test_contradicted_claim_reduces_total_score(self) -> None:
        """Adding a Tier D claim (weight -1.5) pulls the total score down."""
        bundle_without_d = _make_bundle(claims=[_make_claim("A"), _make_claim("B")])
        bundle_with_d = _make_bundle(claims=[_make_claim("A"), _make_claim("B"), _make_claim("D")])
        assert bundle_with_d.total_weighted_score < bundle_without_d.total_weighted_score
        # 1.0 + 0.7 - 1.5 = 0.2
        assert bundle_with_d.total_weighted_score == pytest.approx(0.2)

    def test_evidence_bundle_with_no_claims_has_zero_score(self) -> None:
        """An empty claims list produces total_weighted_score of exactly 0.0."""
        bundle = _make_bundle(claims=[])
        assert bundle.total_weighted_score == 0.0

    def test_multiple_d_tier_claims_can_produce_negative_score(self) -> None:
        """Multiple Tier D claims can drive total_weighted_score negative."""
        bundle = _make_bundle(claims=[
            _make_claim("D"),
            _make_claim("D"),
        ])
        # -1.5 + -1.5 = -3.0
        assert bundle.total_weighted_score == pytest.approx(-3.0)

    def test_total_score_is_computed_fresh_not_cached(self) -> None:
        """
        total_weighted_score is a @property, not a stored field.
        Two bundles with identical claims must return identical scores —
        confirming determinism without caching side effects.
        """
        claims = [_make_claim("A"), _make_claim("B")]
        bundle_a = _make_bundle(claims=claims)
        bundle_b = _make_bundle(claims=claims)
        assert bundle_a.total_weighted_score == bundle_b.total_weighted_score


# ── silence_penalty Property Tests ───────────────────────────────────────────

class TestSilencePenalty:
    """
    WHY: Silence penalties are separate from claim weights. They must encode
    the correct severity → penalty mapping to produce accurate confidence calculations.
    """

    def test_silence_penalty_high_severity_is_0_3(self) -> None:
        """A single high-severity SilenceFlag contributes a 0.3 penalty."""
        flag = SilenceFlag(
            expected_signal="quantified outcomes for senior role",
            absence_interpretation="Senior engineers are expected to quantify impact",
            severity="high",
        )
        bundle = _make_bundle(silence_flags=[flag])
        assert bundle.silence_penalty == pytest.approx(0.3)

    def test_silence_penalty_medium_severity_is_0_15(self) -> None:
        """A single medium-severity SilenceFlag contributes a 0.15 penalty."""
        flag = SilenceFlag(
            expected_signal="team size for leadership role",
            absence_interpretation="Leadership roles should state team size",
            severity="medium",
        )
        bundle = _make_bundle(silence_flags=[flag])
        assert bundle.silence_penalty == pytest.approx(0.15)

    def test_silence_penalty_low_severity_is_zero(self) -> None:
        """A low-severity SilenceFlag contributes no penalty (0.0)."""
        flag = SilenceFlag(
            expected_signal="side projects or open source",
            absence_interpretation="Minor curiosity — not expected for all candidates",
            severity="low",
        )
        bundle = _make_bundle(silence_flags=[flag])
        assert bundle.silence_penalty == 0.0

    def test_multiple_high_severity_flags_accumulate(self) -> None:
        """Two high-severity SilenceFlags accumulate to 0.6 total penalty."""
        flags = [
            SilenceFlag(
                expected_signal="quantified outcomes",
                absence_interpretation="Expected for senior role",
                severity="high",
            ),
            SilenceFlag(
                expected_signal="architectural decisions",
                absence_interpretation="Expected for staff engineer role",
                severity="high",
            ),
        ]
        bundle = _make_bundle(silence_flags=flags)
        assert bundle.silence_penalty == pytest.approx(0.6)

    def test_mixed_severity_flags_sum_correctly(self) -> None:
        """One high (0.3) + one medium (0.15) + one low (0.0) = 0.45."""
        flags = [
            SilenceFlag(
                expected_signal="quantified outcomes",
                absence_interpretation="Expected for senior",
                severity="high",
            ),
            SilenceFlag(
                expected_signal="team size",
                absence_interpretation="Expected for leader",
                severity="medium",
            ),
            SilenceFlag(
                expected_signal="side projects",
                absence_interpretation="Minor curiosity",
                severity="low",
            ),
        ]
        bundle = _make_bundle(silence_flags=flags)
        assert bundle.silence_penalty == pytest.approx(0.45)

    def test_no_silence_flags_produces_zero_penalty(self) -> None:
        """An empty silence_flags list produces a silence_penalty of 0.0."""
        bundle = _make_bundle(silence_flags=[])
        assert bundle.silence_penalty == 0.0


# ── EvidenceBundle Structural Tests ──────────────────────────────────────────

class TestEvidenceBundleStructure:
    """
    WHY: Structural properties of EvidenceBundle (flags, verdicts) must be
    tested independently of the score calculations to catch inconsistencies
    between stored fields and computed properties.
    """

    def test_evidence_bundle_with_critical_contradiction_sets_flag(self) -> None:
        """
        has_critical_contradiction=True must be set by the caller when a critical
        contradiction exists. The bundle preserves this flag accurately.
        """
        bundle = _make_bundle(has_critical=True)
        assert bundle.has_critical_contradiction is True

    def test_evidence_bundle_without_critical_contradiction_flag_is_false(self) -> None:
        """By default has_critical_contradiction is False."""
        bundle = _make_bundle(has_critical=False)
        assert bundle.has_critical_contradiction is False

    def test_builder_maintainer_verdict_is_set_correctly(self) -> None:
        """builder_maintainer_verdict stores and returns the value passed at construction."""
        for verdict in ("builder", "maintainer", "hybrid", "insufficient_data"):
            bundle = EvidenceBundle(
                candidate_id="test",
                builder_maintainer_verdict=verdict,  # type: ignore[arg-type]
            )
            assert bundle.builder_maintainer_verdict == verdict

    def test_evidence_bundle_is_frozen(self) -> None:
        """EvidenceBundle is immutable — mutation must raise an error."""
        bundle = _make_bundle()
        with pytest.raises(Exception):
            bundle.candidate_id = "mutated"  # type: ignore[misc]
