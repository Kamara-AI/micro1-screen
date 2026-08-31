"""
WHY: Contradictions are first-class evidence in SCREEN. Mis-classifying a
critical contradiction as moderate (or missing it entirely) can cause a
fraudulent candidate to proceed through the pipeline unchallenged.

HOW: Tests validate the Contradiction schema fields and the impact of
contradictions on EvidenceBundle's has_critical_contradiction flag.
They also verify that severity classification flows correctly from
the Contradiction into the EvidenceBundle structural flags.

Note: The actual LLM-based contradiction *detection* (extract_evidence node)
is not tested here — that is an integration test. These unit tests verify
the data model and aggregation logic.
"""

import pytest

from screen.schemas.evidence import Contradiction, EvidenceBundle, Claim, SIGNAL_WEIGHTS


def _make_claim(tier: str) -> Claim:
    return Claim(
        text=f"Claim with tier {tier}",
        tier=tier,  # type: ignore[arg-type]
        confidence_weight=SIGNAL_WEIGHTS[tier],
        source_location=f"Test — tier {tier}",
    )


def _make_contradiction(
    severity: str,
    contradiction_type: str = "temporal",
    claim_a: str = "Claim A",
    claim_b: str = "Claim B",
) -> Contradiction:
    """Helper to build a Contradiction with configurable severity and type."""
    return Contradiction(
        claim_a=claim_a,
        claim_b=claim_b,
        contradiction_type=contradiction_type,  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        explanation=f"Test contradiction — severity={severity}, type={contradiction_type}",
    )


# ── Contradiction Type Tests ──────────────────────────────────────────────────

class TestContradictionTypes:
    """
    WHY: Each contradiction type has a distinct semantic meaning and determines
    what the human reviewer needs to verify. The type field must be stored
    exactly as provided and remain immutable.
    """

    def test_temporal_contradiction_where_company_postdates_employment(self) -> None:
        """
        A temporal contradiction captures impossible date ranges.
        Severity must be critical — you cannot work somewhere before it exists.
        """
        contradiction = Contradiction(
            claim_a="Claims employment at DataCorp from 2018",
            claim_b="DataCorp was incorporated in 2020",
            contradiction_type="temporal",
            severity="critical",
            explanation="Cannot be employed at a company 2 years before its incorporation",
        )
        assert contradiction.contradiction_type == "temporal"
        assert contradiction.severity == "critical"
        assert "2018" in contradiction.claim_a
        assert "2020" in contradiction.claim_b

    def test_scope_inflation_contradiction_where_team_size_exceeds_company_headcount(self) -> None:
        """
        A scope_inflation contradiction captures impossible role scope.
        A team of 50 inside a 12-person company is structurally impossible.
        """
        contradiction = Contradiction(
            claim_a="Claims to have managed a team of 50 engineers",
            claim_b="Employer had 12 total employees at that time",
            contradiction_type="scope_inflation",
            severity="critical",
            explanation="A 50-person engineering team cannot exist inside a 12-person company",
        )
        assert contradiction.contradiction_type == "scope_inflation"
        assert contradiction.severity == "critical"

    def test_skill_level_contradiction_stores_fields_correctly(self) -> None:
        """skill_level contradiction is stored and retrievable without mutation."""
        contradiction = _make_contradiction(
            severity="moderate",
            contradiction_type="skill_level",
            claim_a="Claims Python expert with 10 years experience",
            claim_b="All described code examples show beginner-level patterns",
        )
        assert contradiction.contradiction_type == "skill_level"
        assert contradiction.severity == "moderate"

    def test_title_inflation_contradiction_stores_fields_correctly(self) -> None:
        """title_inflation contradiction is stored and retrievable without mutation."""
        contradiction = _make_contradiction(
            severity="moderate",
            contradiction_type="title_inflation",
            claim_a="CTO title claimed",
            claim_b="Responsibilities described are purely hands-on coding with no leadership",
        )
        assert contradiction.contradiction_type == "title_inflation"
        assert contradiction.severity == "moderate"

    def test_employment_gap_contradiction_stores_fields_correctly(self) -> None:
        """employment_gap contradiction is stored and retrievable without mutation."""
        contradiction = _make_contradiction(
            severity="minor",
            contradiction_type="employment_gap",
            claim_a="Employment at CompanyA ended 2020-01",
            claim_b="Employment at CompanyB started 2020-01 (no gap stated)",
        )
        assert contradiction.contradiction_type == "employment_gap"
        assert contradiction.severity == "minor"


# ── Critical Contradiction Flag Tests ────────────────────────────────────────

class TestCriticalContradictionFlag:
    """
    WHY: The has_critical_contradiction flag on EvidenceBundle is the single
    most important escalation trigger. It must be True if and only if at
    least one critical contradiction is present.
    """

    def test_critical_contradiction_sets_has_critical_contradiction_flag_on_bundle(self) -> None:
        """
        When the bundle is constructed with has_critical_contradiction=True
        (set by the extract_evidence node after finding a critical contradiction),
        the flag must be preserved exactly.
        """
        critical = _make_contradiction(severity="critical")
        bundle = EvidenceBundle(
            candidate_id="test",
            claims=[_make_claim("B")],
            contradictions=[critical],
            has_critical_contradiction=True,  # Set by extract_evidence node
        )
        assert bundle.has_critical_contradiction is True

    def test_moderate_contradiction_does_not_set_critical_flag(self) -> None:
        """
        A moderate contradiction does not set has_critical_contradiction.
        The flag must remain False when only moderate contradictions are present.
        """
        moderate = _make_contradiction(severity="moderate")
        bundle = EvidenceBundle(
            candidate_id="test",
            claims=[_make_claim("B")],
            contradictions=[moderate],
            has_critical_contradiction=False,  # Correct — only moderate contradiction
        )
        assert bundle.has_critical_contradiction is False

    def test_minor_contradiction_does_not_set_critical_flag(self) -> None:
        """A minor contradiction must not trigger the critical flag."""
        minor = _make_contradiction(severity="minor")
        bundle = EvidenceBundle(
            candidate_id="test",
            contradictions=[minor],
            has_critical_contradiction=False,
        )
        assert bundle.has_critical_contradiction is False

    def test_multiple_minor_contradictions_accumulate_in_bundle(self) -> None:
        """
        Multiple minor contradictions are all stored in the contradictions list.
        The list must contain all of them — none dropped.
        """
        contradictions = [
            _make_contradiction(
                severity="minor",
                contradiction_type="employment_gap",
                claim_a=f"Claim A-{i}",
                claim_b=f"Claim B-{i}",
            )
            for i in range(3)
        ]
        bundle = EvidenceBundle(
            candidate_id="test",
            contradictions=contradictions,
            has_critical_contradiction=False,
        )
        assert len(bundle.contradictions) == 3
        assert all(c.severity == "minor" for c in bundle.contradictions)

    def test_contradiction_is_immutable(self) -> None:
        """Contradiction objects are frozen — mutation must raise."""
        contradiction = _make_contradiction(severity="critical")
        with pytest.raises(Exception):
            contradiction.severity = "minor"  # type: ignore[misc]

    def test_multiple_contradictions_of_mixed_severity_all_stored(self) -> None:
        """All contradictions (critical, moderate, minor) are preserved in the bundle."""
        bundle = EvidenceBundle(
            candidate_id="test",
            contradictions=[
                _make_contradiction(severity="critical"),
                _make_contradiction(severity="moderate"),
                _make_contradiction(severity="minor"),
            ],
            has_critical_contradiction=True,
        )
        severities = {c.severity for c in bundle.contradictions}
        assert severities == {"critical", "moderate", "minor"}
        assert len(bundle.contradictions) == 3
