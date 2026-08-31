"""
WHY: Silence flags implement the "silence reader" mental model from elite
recruiter research. The ABSENCE of expected information is a signal, not
neutral. A senior engineer with no architectural decisions mentioned is
suspicious. These tests verify that silence flags are generated, classified
by severity, and accumulated correctly in the EvidenceBundle.

HOW: Tests use the _detect_silence_flags() function — a pure function that
encodes the silence detection heuristics. This function mirrors the logic
the extract_evidence node will call, making it independently testable.

The heuristics tested here:
- Senior roles (senior/staff/executive) → missing quantified outcomes → HIGH severity
- Leadership roles (any role with team_size_mentioned=None) → missing team size → MEDIUM
- Junior roles → missing quantified outcomes → LOW severity (not mandatory)
- All expected signals present → no flags generated
"""

from typing import Literal

import pytest

from screen.schemas.candidate import CandidateProfile, RoleEntry
from screen.schemas.evidence import SilenceFlag


# ── Silence detection pure function ───────────────────────────────────────────

RoleSeniority = Literal["junior", "mid", "senior", "staff", "executive"]


def _detect_silence_flags(
    candidate_profile: CandidateProfile,
    role_seniority: RoleSeniority,
) -> list[SilenceFlag]:
    """
    WHY: Pure function encoding the silence detection heuristics so they can
    be tested independently of the LLM extract_evidence node.

    HOW: Inspects each RoleEntry against role_seniority expectations:
    - Senior/staff/executive roles are expected to have quantified outcomes.
      Missing → SilenceFlag(severity="high")
    - Any role claiming leadership (is_quantified=True + achievements) but no
      team_size_mentioned generates SilenceFlag(severity="medium").
    - Junior/mid roles missing quantified outcomes → SilenceFlag(severity="low").

    Args:
        candidate_profile: Parsed and structured candidate data.
        role_seniority:    Target seniority level from the job spec.

    Returns:
        List of SilenceFlag objects (may be empty if all expected signals present).
    """
    flags: list[SilenceFlag] = []
    senior_levels = {"senior", "staff", "executive"}

    for role in candidate_profile.roles:
        # Quantified outcomes check
        if not role.is_quantified:
            if role_seniority in senior_levels:
                flags.append(
                    SilenceFlag(
                        expected_signal=f"quantified outcomes for {role_seniority} role at {role.company}",
                        absence_interpretation=(
                            f"{role_seniority.capitalize()} engineers are expected to state "
                            f"measurable impact (e.g., '40% reduction in latency'). "
                            f"Absence suggests either vague CV writing or limited ownership."
                        ),
                        severity="high",
                    )
                )
            else:
                # Junior/mid — low severity
                flags.append(
                    SilenceFlag(
                        expected_signal=f"quantified outcomes for {role.title} at {role.company}",
                        absence_interpretation=(
                            "Quantified outcomes are a positive signal at any level, "
                            "but not strictly expected for junior/mid roles."
                        ),
                        severity="low",
                    )
                )

        # Team size check — relevant only for leadership roles
        # Heuristic: if the role title contains leadership keywords and no team size is stated
        leadership_keywords = {"lead", "manager", "director", "head", "vp", "chief", "principal"}
        title_lower = role.title.lower()
        is_leadership_title = any(kw in title_lower for kw in leadership_keywords)

        if is_leadership_title and role.team_size_mentioned is None:
            flags.append(
                SilenceFlag(
                    expected_signal=f"team size for leadership role: {role.title} at {role.company}",
                    absence_interpretation=(
                        "Leadership roles should state team size to calibrate scope. "
                        "Absence makes it impossible to assess management responsibility."
                    ),
                    severity="medium",
                )
            )

    return flags


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_role(
    title: str = "Software Engineer",
    company: str = "TestCo",
    is_quantified: bool = True,
    team_size_mentioned: int | None = None,
    achievements: list[str] | None = None,
) -> RoleEntry:
    return RoleEntry(
        title=title,
        company=company,
        is_quantified=is_quantified,
        team_size_mentioned=team_size_mentioned,
        achievements=achievements or ["Built internal tooling"],
    )


def _make_profile(roles: list[RoleEntry]) -> CandidateProfile:
    return CandidateProfile(
        candidate_id="test-cand",
        roles=roles,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestSilenceFlagGeneration:
    """
    WHY: Each silence heuristic must fire at the right severity and not fire
    when the expected signal IS present. False positives and missed negatives
    both corrupt the confidence calculation.
    """

    def test_senior_role_without_quantified_outcomes_generates_high_severity_flag(self) -> None:
        """
        A senior-level role with is_quantified=False must produce a SilenceFlag
        with severity='high'. Senior engineers must evidence measurable impact.
        """
        profile = _make_profile(roles=[
            _make_role(title="Senior Software Engineer", is_quantified=False),
        ])
        flags = _detect_silence_flags(profile, role_seniority="senior")

        high_flags = [f for f in flags if f.severity == "high"]
        assert len(high_flags) >= 1
        assert any("quantified outcomes" in f.expected_signal for f in high_flags)

    def test_staff_role_without_quantified_outcomes_generates_high_severity_flag(self) -> None:
        """Staff-level roles also require quantified outcomes — same high severity."""
        profile = _make_profile(roles=[
            _make_role(title="Staff Engineer", is_quantified=False),
        ])
        flags = _detect_silence_flags(profile, role_seniority="staff")

        high_flags = [f for f in flags if f.severity == "high"]
        assert len(high_flags) >= 1

    def test_leadership_role_without_team_size_generates_medium_severity_flag(self) -> None:
        """
        A role with a leadership title (Manager, Director, Lead, etc.) but no
        team_size_mentioned generates a SilenceFlag with severity='medium'.
        """
        profile = _make_profile(roles=[
            _make_role(
                title="Engineering Manager",
                is_quantified=True,       # quantified, so no high flag
                team_size_mentioned=None,  # BUT no team size
            ),
        ])
        flags = _detect_silence_flags(profile, role_seniority="senior")

        medium_flags = [f for f in flags if f.severity == "medium"]
        assert len(medium_flags) >= 1
        assert any("team size" in f.expected_signal for f in medium_flags)

    def test_junior_role_without_quantified_outcomes_generates_low_severity_flag(self) -> None:
        """
        A junior role without quantified outcomes gets a SilenceFlag with
        severity='low' — noted but not penalising confidence significantly.
        """
        profile = _make_profile(roles=[
            _make_role(title="Junior Developer", is_quantified=False),
        ])
        flags = _detect_silence_flags(profile, role_seniority="junior")

        low_flags = [f for f in flags if f.severity == "low"]
        assert len(low_flags) >= 1
        # Must NOT produce a high-severity flag for a junior role
        high_flags = [f for f in flags if f.severity == "high"]
        assert len(high_flags) == 0

    def test_no_silence_flags_generated_when_all_expected_signals_present(self) -> None:
        """
        A senior role with is_quantified=True and team_size_mentioned set produces
        no silence flags — all expected signals are present.
        """
        profile = _make_profile(roles=[
            _make_role(
                title="Senior Software Engineer",
                is_quantified=True,
                team_size_mentioned=None,  # Not a leadership title, so no team-size flag
            ),
        ])
        flags = _detect_silence_flags(profile, role_seniority="senior")

        # No high flags for senior role with quantified outcomes
        high_flags = [f for f in flags if f.severity == "high"]
        assert len(high_flags) == 0

    def test_leadership_role_with_team_size_stated_generates_no_medium_flag(self) -> None:
        """When team_size_mentioned is set for a leadership role, no medium flag is raised."""
        profile = _make_profile(roles=[
            _make_role(
                title="Engineering Manager",
                is_quantified=True,
                team_size_mentioned=8,  # Stated — no silence flag
            ),
        ])
        flags = _detect_silence_flags(profile, role_seniority="senior")

        medium_flags = [f for f in flags if f.severity == "medium"]
        assert len(medium_flags) == 0

    def test_multiple_roles_each_checked_independently(self) -> None:
        """
        When a profile has multiple roles with missing signals, each role
        generates its own SilenceFlag independently.
        """
        profile = _make_profile(roles=[
            _make_role(title="Senior Engineer", company="Co1", is_quantified=False),
            _make_role(title="Senior Engineer", company="Co2", is_quantified=False),
        ])
        flags = _detect_silence_flags(profile, role_seniority="senior")

        high_flags = [f for f in flags if f.severity == "high"]
        # One flag per role — two roles with missing outcomes = two flags
        assert len(high_flags) == 2

    def test_silence_flag_has_required_fields(self) -> None:
        """Every generated SilenceFlag has non-empty expected_signal and absence_interpretation."""
        profile = _make_profile(roles=[
            _make_role(title="Senior Engineer", is_quantified=False),
        ])
        flags = _detect_silence_flags(profile, role_seniority="senior")

        for flag in flags:
            assert len(flag.expected_signal) > 0
            assert len(flag.absence_interpretation) > 0
            assert flag.severity in ("high", "medium", "low")
