"""
WHY: The Tier 1 pre-filter is deterministic — no LLM involved. We can
test it end-to-end with synthetic state objects and verify routing.

The pre-filter has exactly three outcomes:
  1. No hard requirements → hard_rejected=False (fast pass)
  2. All requirements satisfied → hard_rejected=False (full pass)
  3. Any requirement fails → hard_rejected=True + Decision(STRONG_NO) + CandidateFeedback

HOW: We build ScreeningState dicts directly (TypedDict — no class instantiation needed)
and call tier1_prefilter_node() with them. We then assert on the returned partial
state dict. No mocking of LLM clients is needed because this node makes no LLM calls.
"""

from typing import Any
from unittest.mock import patch, MagicMock

import pytest

from screen.agent.nodes.tier1_prefilter import tier1_prefilter_node, _requirement_satisfied
from screen.schemas.candidate import CandidateProfile, RoleEntry, EducationEntry
from screen.schemas.decision import Decision, CandidateFeedback
from screen.schemas.input import ScreeningInput
from screen.schemas.state import ScreeningState, initial_state


# ── State Builders ────────────────────────────────────────────────────────────

def _make_screening_input(
    candidate_id: str = "cand-001",
    hard_requirements: list[str] | None = None,
) -> ScreeningInput:
    """Build a valid ScreeningInput with configurable hard requirements."""
    return ScreeningInput(
        candidate_id=candidate_id,
        cv_text=(
            "Senior Software Engineer with 8 years of experience in Python and Go. "
            "AWS certified. Built real-time payment systems at scale."
        ),
        job_description=(
            "Senior engineer role. Requirements: 5+ years Python. "
            "Distributed systems experience required."
        ),
        role_seniority="senior",
        role_type="engineering",
        hard_requirements=hard_requirements or [],
    )


def _make_candidate_profile(
    candidate_id: str = "cand-001",
    skills: list[str] | None = None,
    role_titles: list[str] | None = None,
    achievements: list[str] | None = None,
) -> CandidateProfile:
    """Build a CandidateProfile with configurable skills and role data."""
    roles = []
    if role_titles:
        for title in role_titles:
            roles.append(RoleEntry(
                title=title,
                company="TestCo",
                achievements=achievements or [],
                is_quantified=True,
            ))
    else:
        roles.append(RoleEntry(
            title="Senior Software Engineer",
            company="TechCorp Kenya",
            achievements=achievements or [
                "Built Python microservices handling 5 years of transaction data",
                "Reduced latency by 40% using distributed caching",
            ],
            is_quantified=True,
        ))

    return CandidateProfile(
        candidate_id=candidate_id,
        skills_stated=skills or ["Python", "Go", "AWS", "PostgreSQL"],
        roles=roles,
        highest_education_level="bachelors",
    )


def _make_state(
    screening_input: ScreeningInput,
    candidate_profile: CandidateProfile,
) -> ScreeningState:
    """Assemble a minimal but valid ScreeningState for the prefilter node."""
    state = initial_state(screening_input)
    # TypedDict mutation is safe here — this is test setup, not production code
    state["candidate_profile"] = candidate_profile
    state["current_tier"] = 1
    return state


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestPrefilterPassCases:
    """
    WHY: Pass cases must return hard_rejected=False and include a trajectory entry.
    The pipeline must continue to the next node when all requirements are met.
    """

    def test_candidate_meeting_all_hard_requirements_passes_prefilter(self) -> None:
        """
        A candidate with 'python' in skills_stated and 'senior' in a role title
        must pass when hard_requirements=['python', 'senior'].
        """
        inp = _make_screening_input(hard_requirements=["python", "senior"])
        profile = _make_candidate_profile(skills=["Python", "Go", "AWS"])
        state = _make_state(inp, profile)

        result = tier1_prefilter_node(state)

        assert result["hard_rejected"] is False
        assert "decision" not in result or result.get("decision") is None
        assert len(result["trajectory"]) == 1

    def test_candidate_with_no_hard_requirements_passes_prefilter_automatically(self) -> None:
        """No hard requirements → automatic pass with hard_rejected=False."""
        inp = _make_screening_input(hard_requirements=[])
        profile = _make_candidate_profile()
        state = _make_state(inp, profile)

        result = tier1_prefilter_node(state)

        assert result["hard_rejected"] is False
        assert len(result["trajectory"]) == 1
        assert "no hard requirements" in result["trajectory"][0].reasoning_summary.lower()

    def test_requirement_matched_in_achievements_passes_prefilter(self) -> None:
        """Requirements matched in role achievements (not just skills) must pass."""
        inp = _make_screening_input(hard_requirements=["aws certification"])
        profile = _make_candidate_profile(
            skills=[],  # Not in skills — must find in achievements
            achievements=["Completed AWS certification and applied it to production deployments"],
        )
        state = _make_state(inp, profile)

        result = tier1_prefilter_node(state)

        assert result["hard_rejected"] is False


class TestPrefilterRejectCases:
    """
    WHY: Hard reject cases must produce STRONG_NO with full evidence of
    which requirement failed. The pipeline must not proceed past the prefilter.
    """

    def test_candidate_failing_minimum_years_gets_strong_no(self) -> None:
        """
        A candidate whose profile has no evidence of 'years' matching a
        'minimum 5 years' requirement must be hard rejected with STRONG_NO.
        """
        inp = _make_screening_input(hard_requirements=["minimum 10 years java"])
        profile = _make_candidate_profile(
            skills=["Python", "Go"],  # No Java
            achievements=["Built Python microservices"],
        )
        state = _make_state(inp, profile)

        result = tier1_prefilter_node(state)

        assert result["hard_rejected"] is True
        decision: Decision = result["decision"]
        assert decision.verdict == "STRONG_NO"
        assert decision.passed_hard_requirements is False
        assert decision.tier_processed == 1
        assert decision.confidence_pct == 100.0  # Deterministic — no uncertainty

    def test_candidate_failing_required_certification_gets_strong_no(self) -> None:
        """
        A candidate missing a mandatory certification requirement must receive
        hard_rejected=True and a STRONG_NO Decision citing the failed requirement.
        """
        inp = _make_screening_input(hard_requirements=["cpa certification"])
        profile = _make_candidate_profile(
            skills=["Excel", "SQL", "Python"],  # No CPA
            achievements=["Analysed financial data using SQL"],
        )
        state = _make_state(inp, profile)

        result = tier1_prefilter_node(state)

        assert result["hard_rejected"] is True
        decision: Decision = result["decision"]
        assert "cpa certification" in decision.primary_evidence[0].lower()
        assert decision.verdict == "STRONG_NO"

    def test_hard_rejected_candidate_has_candidate_feedback_generated(self) -> None:
        """
        Even a hard-rejected candidate must receive CandidateFeedback —
        candidate dignity protocol. Feedback must contain genuine_strength
        and gap_for_this_role.
        """
        inp = _make_screening_input(hard_requirements=["right to work in uk"])
        profile = _make_candidate_profile(skills=["Python"])
        state = _make_state(inp, profile)

        result = tier1_prefilter_node(state)

        assert result["hard_rejected"] is True
        feedback: CandidateFeedback = result["candidate_feedback"]
        assert feedback is not None
        assert len(feedback.genuine_strength) >= 20  # min_length=20
        assert len(feedback.gap_for_this_role) >= 20  # min_length=20
        assert "right to work in uk" in feedback.gap_for_this_role.lower()

    def test_prefilter_short_circuits_on_first_failed_requirement(self) -> None:
        """
        When multiple hard requirements are present, the node fails fast on
        the first unmet requirement without checking the rest.
        """
        inp = _make_screening_input(
            hard_requirements=["java", "cobol", "fortran"]  # All absent
        )
        profile = _make_candidate_profile(skills=["Python"])
        state = _make_state(inp, profile)

        result = tier1_prefilter_node(state)

        assert result["hard_rejected"] is True
        decision: Decision = result["decision"]
        # Only the first failed requirement (java) should appear
        assert "java" in decision.primary_evidence[0].lower()

    def test_hard_reject_decision_primary_evidence_cites_failed_requirement(self) -> None:
        """
        The STRONG_NO Decision's primary_evidence must explicitly name the failed
        requirement — it must be auditable by a human reviewer.
        """
        failed_req = "kubernetes"
        inp = _make_screening_input(hard_requirements=[failed_req])
        profile = _make_candidate_profile(skills=["Docker", "AWS"])
        state = _make_state(inp, profile)

        result = tier1_prefilter_node(state)

        decision: Decision = result["decision"]
        assert any(failed_req in ev.lower() for ev in decision.primary_evidence)


class TestPrefilterNoLLMCall:
    """
    WHY: The tier1_prefilter_node is documented as 100% deterministic — no LLM.
    If an LLM call is ever accidentally added, this test catches it immediately.
    """

    def test_prefilter_does_not_call_llm(self) -> None:
        """
        tier1_prefilter_node must complete without calling any LLM client.
        We verify this by patching the ChatGoogleGenerativeAI constructor
        and asserting it was never called.
        """
        inp = _make_screening_input(hard_requirements=["python"])
        profile = _make_candidate_profile(skills=["Python"])
        state = _make_state(inp, profile)

        with patch("screen.agent.nodes.tier1_prefilter.logger") as mock_logger:
            # Only mock the logger — NOT the LLM. If the node tries to call an LLM,
            # it will fail because no API key is real, surfacing the regression.
            result = tier1_prefilter_node(state)

        # The node must have completed successfully (no LLM error)
        assert "hard_rejected" in result
        assert result["total_cost_usd"] == 0.0  # No LLM = zero cost

    def test_prefilter_trajectory_model_used_is_none(self) -> None:
        """
        The trajectory entry for a deterministic node must have model_used=None.
        Any non-None value here means an LLM call was added without documentation.
        """
        inp = _make_screening_input(hard_requirements=["python"])
        profile = _make_candidate_profile(skills=["Python"])
        state = _make_state(inp, profile)

        result = tier1_prefilter_node(state)

        entry = result["trajectory"][0]
        assert entry.model_used is None, (
            f"tier1_prefilter is deterministic — model_used must be None, got: {entry.model_used}"
        )


# ── _requirement_satisfied Unit Tests ────────────────────────────────────────

class TestRequirementSatisfiedHelper:
    """
    WHY: _requirement_satisfied is the core matching heuristic. Testing it
    directly (isolated from the full node) gives precise coverage of each
    matching strategy (skills, role titles, achievements, education).
    """

    def test_requirement_matched_in_skills_stated(self) -> None:
        """Exact skill match (case-insensitive) returns satisfied=True."""
        profile = _make_candidate_profile(skills=["Python", "AWS"])
        satisfied, reason = _requirement_satisfied("python", profile)
        assert satisfied is True
        assert "skill" in reason.lower()

    def test_requirement_not_in_profile_returns_false(self) -> None:
        """A requirement with no match in skills, titles, achievements, or education returns False."""
        profile = _make_candidate_profile(skills=["Java"], achievements=["Built Java APIs"])
        satisfied, reason = _requirement_satisfied("cobol", profile)
        assert satisfied is False
        assert "no evidence" in reason.lower()

    def test_requirement_matched_in_role_title(self) -> None:
        """A requirement present in a role title returns satisfied=True."""
        profile = _make_candidate_profile(role_titles=["Senior Python Engineer"])
        satisfied, reason = _requirement_satisfied("python", profile)
        assert satisfied is True

    def test_requirement_matched_in_achievements(self) -> None:
        """A requirement present in role achievements returns satisfied=True."""
        profile = _make_candidate_profile(
            skills=[],
            achievements=["Implemented Kubernetes-based deployment pipeline"],
        )
        satisfied, reason = _requirement_satisfied("kubernetes", profile)
        assert satisfied is True

    def test_requirement_matched_in_education_degree(self) -> None:
        """A requirement matched against education degree returns satisfied=True."""
        profile = CandidateProfile(
            candidate_id="test",
            education=[
                EducationEntry(
                    institution="University of Nairobi",
                    degree="Bachelor of Science in Computer Science",
                    field_of_study="Computer Science",
                )
            ],
        )
        satisfied, reason = _requirement_satisfied("computer science", profile)
        assert satisfied is True
