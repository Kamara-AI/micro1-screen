"""
WHY: Schema validation is the first line of defence. Invalid input caught
at the schema boundary never reaches the LLM or the decision logic.
These tests verify Pydantic validators, field constraints, computed properties,
and immutability across all core schemas.

HOW: Each test constructs a schema with a deliberate violation and verifies
that pydantic.ValidationError is raised (or not raised for valid inputs).
We test field constraints (min_length, ge/le bounds), custom validators
(candidate_id_no_spaces), and schema immutability (frozen=True).
"""

import pytest
from pydantic import ValidationError

from screen.schemas.candidate import CandidateProfile, RoleEntry
from screen.schemas.decision import Decision, HumanBrief
from screen.schemas.evidence import Claim, EvidenceBundle, SIGNAL_WEIGHTS
from screen.schemas.input import ScreeningInput


# ── ScreeningInput Validation Tests ──────────────────────────────────────────

class TestScreeningInputValidation:
    """
    WHY: ScreeningInput is the pipeline entry point. Any invalid input
    that slips through here corrupts every downstream node's outputs.
    """

    def test_screening_input_rejects_candidate_id_with_spaces(self) -> None:
        """candidate_id containing spaces must raise ValidationError (field_validator)."""
        with pytest.raises(ValidationError) as exc_info:
            ScreeningInput(
                candidate_id="cand 001",  # Space in ID — invalid
                cv_text="A" * 60,
                job_description="B" * 60,
                role_seniority="senior",
                role_type="engineering",
            )
        assert "spaces" in str(exc_info.value).lower() or "candidate_id" in str(exc_info.value)

    def test_screening_input_rejects_cv_text_shorter_than_50_chars(self) -> None:
        """cv_text shorter than 50 characters must raise ValidationError (min_length=50)."""
        with pytest.raises(ValidationError):
            ScreeningInput(
                candidate_id="cand-001",
                cv_text="Too short",  # 9 chars — under minimum
                job_description="B" * 60,
                role_seniority="senior",
                role_type="engineering",
            )

    def test_screening_input_rejects_empty_candidate_id(self) -> None:
        """An empty candidate_id must fail validation (min_length=1)."""
        with pytest.raises(ValidationError):
            ScreeningInput(
                candidate_id="",
                cv_text="A" * 60,
                job_description="B" * 60,
                role_seniority="senior",
                role_type="engineering",
            )

    def test_screening_input_accepts_valid_candidate_without_spaces(self) -> None:
        """A valid candidate_id (no spaces, correct length) must not raise."""
        inp = ScreeningInput(
            candidate_id="cand-001",
            cv_text="A" * 60,
            job_description="B" * 60,
            role_seniority="senior",
            role_type="engineering",
        )
        assert inp.candidate_id == "cand-001"

    def test_screening_input_rejects_job_description_shorter_than_50_chars(self) -> None:
        """job_description shorter than 50 characters must raise ValidationError."""
        with pytest.raises(ValidationError):
            ScreeningInput(
                candidate_id="cand-001",
                cv_text="A" * 60,
                job_description="Too short JD",
                role_seniority="senior",
                role_type="engineering",
            )

    def test_screening_input_rejects_invalid_role_seniority(self) -> None:
        """role_seniority must be one of the defined Literal values."""
        with pytest.raises(ValidationError):
            ScreeningInput(
                candidate_id="cand-001",
                cv_text="A" * 60,
                job_description="B" * 60,
                role_seniority="intern",  # Not a valid literal
                role_type="engineering",
            )


# ── CandidateProfile Immutability Tests ──────────────────────────────────────

class TestCandidateProfileImmutability:
    """
    WHY: CandidateProfile is frozen — once parsed, it must not be mutated.
    If nodes could mutate it, they'd corrupt each other's view of the candidate.
    """

    def test_candidate_profile_is_immutable_frozen_model(self) -> None:
        """Any attempt to mutate a CandidateProfile field must raise an error."""
        profile = CandidateProfile(candidate_id="cand-001")
        with pytest.raises(Exception):  # ValidationError or TypeError from frozen model
            profile.candidate_id = "mutated"  # type: ignore[misc]

    def test_role_entry_is_immutable_frozen_model(self) -> None:
        """RoleEntry is also frozen — mutations must raise."""
        role = RoleEntry(title="Senior Engineer", company="TestCo")
        with pytest.raises(Exception):
            role.title = "Junior Engineer"  # type: ignore[misc]


# ── EvidenceBundle Computed Property Tests ────────────────────────────────────

class TestEvidenceBundleComputedProperty:
    """
    WHY: total_weighted_score must be a computed property, not a stored field.
    If it were stored, stale values could cause silent miscalculations.
    """

    def test_evidence_bundle_total_weighted_score_is_computed_property_not_stored(self) -> None:
        """
        total_weighted_score must not appear in model_fields (stored fields).
        It must only be accessible as a property computed from the claims list.
        """
        bundle = EvidenceBundle(
            candidate_id="test",
            claims=[
                Claim(
                    text="Test claim",
                    tier="A",
                    confidence_weight=1.0,
                    source_location="Test",
                )
            ],
        )
        # Must be accessible as a property
        assert bundle.total_weighted_score == 1.0

        # Must NOT be in stored model fields (would indicate it's a stored field)
        stored_fields = EvidenceBundle.model_fields
        assert "total_weighted_score" not in stored_fields

    def test_evidence_bundle_silence_penalty_is_computed_property_not_stored(self) -> None:
        """silence_penalty must also be a computed property, not a stored field."""
        stored_fields = EvidenceBundle.model_fields
        assert "silence_penalty" not in stored_fields


# ── SIGNAL_WEIGHTS Map Tests ──────────────────────────────────────────────────

class TestSignalWeightsMap:
    """
    WHY: SIGNAL_WEIGHTS is the numeric backbone of the entire confidence formula.
    If any weight is wrong, every confidence calculation is wrong.
    These values are documented in the schema and must never drift silently.
    """

    def test_signal_weights_map_has_correct_values(self) -> None:
        """SIGNAL_WEIGHTS must contain A=1.0, B=0.7, C=0.1, D=-1.5.
        WHY C=0.1: vague claims carry minimal positive signal (floor effect only).
        They should not move a candidate upward meaningfully — only prevent a
        full zero-contribution floor when the candidate has some effort visible."""
        assert SIGNAL_WEIGHTS["A"] == pytest.approx(1.0)
        assert SIGNAL_WEIGHTS["B"] == pytest.approx(0.7)
        assert SIGNAL_WEIGHTS["C"] == pytest.approx(0.1)
        assert SIGNAL_WEIGHTS["D"] == pytest.approx(-1.5)

    def test_signal_weights_map_has_exactly_four_tiers(self) -> None:
        """SIGNAL_WEIGHTS must cover exactly the four tiers A, B, C, D — no more, no less."""
        assert set(SIGNAL_WEIGHTS.keys()) == {"A", "B", "C", "D"}

    def test_tier_d_is_the_only_negative_weight(self) -> None:
        """Only Tier D has a negative weight — C is zero (neutral), not negative."""
        negative_tiers = [k for k, v in SIGNAL_WEIGHTS.items() if v < 0]
        assert negative_tiers == ["D"]

    def test_tier_a_has_highest_weight(self) -> None:
        """Tier A must have the highest weight of all tiers."""
        assert SIGNAL_WEIGHTS["A"] == max(SIGNAL_WEIGHTS.values())


# ── Decision Validation Tests ─────────────────────────────────────────────────

class TestDecisionValidation:
    """
    WHY: Decision is the final output. Its field constraints must enforce
    that confidence_pct is always within [0, 100] and required fields are present.
    """

    def test_decision_confidence_pct_is_bounded_0_to_100(self) -> None:
        """confidence_pct outside [0, 100] must raise ValidationError."""
        with pytest.raises(ValidationError):
            Decision(
                candidate_id="cand-001",
                verdict="YES",
                confidence_pct=101.0,  # Above ceiling
                primary_evidence=["evidence 1"],
                tier_processed=2,
                estimated_cost_usd=0.01,
                processing_time_ms=500,
                passed_hard_requirements=True,
            )

        with pytest.raises(ValidationError):
            Decision(
                candidate_id="cand-001",
                verdict="YES",
                confidence_pct=-1.0,  # Below floor
                primary_evidence=["evidence 1"],
                tier_processed=2,
                estimated_cost_usd=0.01,
                processing_time_ms=500,
                passed_hard_requirements=True,
            )

    def test_decision_with_valid_fields_is_accepted(self) -> None:
        """A properly formed Decision must not raise any validation error."""
        decision = Decision(
            candidate_id="cand-001",
            verdict="STRONG_YES",
            confidence_pct=85.0,
            primary_evidence=["High-quality evidence claim 1"],
            tier_processed=2,
            estimated_cost_usd=0.015,
            processing_time_ms=1200,
            passed_hard_requirements=True,
        )
        assert decision.verdict == "STRONG_YES"
        assert decision.confidence_pct == 85.0


# ── HumanBrief Validation Tests ───────────────────────────────────────────────

class TestHumanBriefValidation:
    """
    WHY: HumanBrief is the escalation output that a human reviewer reads.
    Each list field must have at least one item — an empty brief is useless
    and signals a pipeline error.
    """

    def test_human_brief_requires_at_least_one_item_in_each_list(self) -> None:
        """Empty what_we_know, what_we_cannot_verify, or verification_tasks must raise."""
        with pytest.raises(ValidationError):
            HumanBrief(
                candidate_id="cand-001",
                escalation_category="critical_contradiction",
                summary="Test contradiction found.",
                what_we_know=[],  # EMPTY — must raise
                what_we_cannot_verify=["Cannot verify founding date"],
                verification_tasks=["Check Companies House"],
                suggested_interview_questions=["Q1", "Q2"],
                first_question="Tell me about DataCorp.",
                risk_to_probe="The founding date discrepancy suggests fabrication.",
            )

    def test_human_brief_with_all_required_fields_is_valid(self) -> None:
        """A properly formed HumanBrief with all required lists populated is valid."""
        brief = HumanBrief(
            candidate_id="cand-001",
            escalation_category="critical_contradiction",
            summary="A critical temporal contradiction was detected.",
            what_we_know=["Claims 8 years experience at scale"],
            what_we_cannot_verify=["Cannot verify DataCorp founding date"],
            verification_tasks=["Check Companies House for DataCorp incorporation date"],
            suggested_interview_questions=["When exactly did you join DataCorp?", "Who was CEO at founding?"],
            first_question="Tell me about your role at DataCorp — specifically when you started.",
            risk_to_probe="If DataCorp was founded in 2020, candidate could not have joined in 2018.",
        )
        assert brief.candidate_id == "cand-001"
        assert brief.escalation_category == "critical_contradiction"
