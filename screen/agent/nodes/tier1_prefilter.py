"""
WHY: Node 2 — the deterministic gatekeeper. No LLM call here. Hard requirements
are binary: either the candidate satisfies them or they don't. Using an LLM for
this would introduce hallucination risk on the highest-stakes check in the pipeline.

Hard requirements are knockout criteria set by the hiring team — e.g., "right to
work in UK", "minimum 5 years Python", "must have active CPA". A candidate who
fails any one of these cannot proceed regardless of how strong their profile is.

HOW: The node reads hard_requirements from ScreeningInput and checks each one
against the candidate's skills_stated and role descriptions. The matching is
heuristic (substring + keyword) — more sophisticated matching can be layered on
later. A single failure triggers hard_rejected=True and a STRONG_NO Decision.
"""

import time
from typing import Any

from screen.core.config import settings
from screen.core.exceptions import StateTransitionError
from screen.core.logging_config import get_logger
from screen.core.trajectory import make_trajectory_entry
from screen.schemas.candidate import CandidateProfile
from screen.schemas.decision import CandidateFeedback, Decision
from screen.schemas.state import ScreeningState

logger = get_logger(__name__)


def _requirement_satisfied(
    requirement: str,
    candidate_profile: CandidateProfile,
) -> tuple[bool, str]:
    """
    WHY: Isolated matching logic keeps the node function clean and makes this
    heuristic independently testable.

    HOW: Checks the requirement keyword against:
    1. skills_stated list (exact and case-insensitive substring)
    2. All role achievement bullet points (keyword presence)
    3. Role titles (for seniority/title requirements)

    Returns (satisfied: bool, reason: str) so callers know WHY a requirement failed.
    """
    req_lower = requirement.lower()

    # Check skills_stated
    for skill in candidate_profile.skills_stated:
        if req_lower in skill.lower() or skill.lower() in req_lower:
            return True, f"Skill '{skill}' found in stated skills"

    # Check role titles and achievements
    for role in candidate_profile.roles:
        if req_lower in role.title.lower():
            return True, f"Requirement matched in role title: {role.title}"
        for achievement in role.achievements:
            if req_lower in achievement.lower():
                return True, f"Requirement matched in role achievements at {role.company}"

    # Check education for credential requirements
    for edu in candidate_profile.education:
        if req_lower in (edu.degree or "").lower():
            return True, f"Requirement matched in education: {edu.degree}"
        if req_lower in (edu.field_of_study or "").lower():
            return True, f"Requirement matched in field of study: {edu.field_of_study}"

    return False, f"No evidence of '{requirement}' found in profile"


def _build_hard_reject_decision(
    candidate_id: str,
    failed_requirement: str,
    failure_reason: str,
    processing_time_ms: int,
    cost_usd: float,
) -> Decision:
    """
    WHY: Produces a minimal STRONG_NO Decision when a hard requirement fails.
    The Decision is constructed here rather than in make_decision_node because
    hard rejects short-circuit the full pipeline — make_decision never runs.

    HOW: Tier 1 decision — cost is near zero (no LLM calls). The primary_evidence
    cites exactly which requirement failed, making the rejection fully auditable.
    """
    return Decision(
        candidate_id=candidate_id,
        verdict="STRONG_NO",
        confidence_pct=100.0,  # Deterministic — no uncertainty
        primary_evidence=[
            f"Hard requirement not met: '{failed_requirement}'",
            failure_reason,
            "Tier 1 pre-filter: automatic rejection — no further analysis performed",
        ],
        escalation_reason=None,
        escalation_category=None,
        tier_processed=1,
        estimated_cost_usd=cost_usd,
        processing_time_ms=processing_time_ms,
        passed_hard_requirements=False,
    )


def _build_hard_reject_feedback(
    candidate_id: str,
    failed_requirement: str,
) -> CandidateFeedback:
    """
    WHY: Even hard-rejected candidates receive feedback — this is the candidate
    dignity protocol. We give them one specific strength and an honest gap.

    However, at Tier 1 we have only the CandidateProfile (no evidence bundle or
    fit analysis), so the feedback is necessarily brief. For hard rejects the
    gap is always the specific failed requirement — honest and actionable.
    """
    return CandidateFeedback(
        candidate_id=candidate_id,
        verdict_communicated="not selected for this role at this time",
        genuine_strength=(
            "Your application was reviewed and your background was considered. "
            "We recognise the experience and skills you have built in your career."
        ),
        gap_for_this_role=(
            f"This role has a specific mandatory requirement that was not evidenced "
            f"in your application: {failed_requirement}. This is a non-negotiable "
            f"criterion for this position."
        ),
        encouragement=(
            "If you believe you do meet this requirement, please reapply and ensure "
            "the relevant experience is clearly stated in your CV."
        ),
    )


def tier1_prefilter_node(state: ScreeningState) -> dict[str, Any]:
    """
    WHY: Deterministic hard-requirement gate. No LLM call — pure Python logic.
    Fast, cheap, and binary. Candidates who fail here cost almost nothing to process.

    HOW:
    1. Validate required state fields are present
    2. Iterate through each hard requirement
    3. On first failure: set hard_rejected=True, create Decision and CandidateFeedback
    4. If all pass: return hard_rejected=False (pipeline continues to extract_evidence)

    DESIGN NOTE: We short-circuit on the first failure. One failed hard requirement
    is sufficient — there is no value in checking the remaining ones.
    """
    node_name = "tier1_prefilter"
    start_ms = time.time() * 1000

    screening_input = state.get("screening_input")
    if screening_input is None:
        raise StateTransitionError(node_name, "screening_input")

    candidate_profile = state.get("candidate_profile")
    if candidate_profile is None:
        raise StateTransitionError(node_name, "candidate_profile")

    candidate_id = screening_input.candidate_id
    hard_requirements = screening_input.hard_requirements

    logger.info(
        "tier1_prefilter started",
        node=node_name,
        candidate_id=candidate_id,
        num_requirements=len(hard_requirements),
    )

    # No hard requirements — pass automatically
    if not hard_requirements:
        trajectory_entry = make_trajectory_entry(
            node=node_name,
            start_time_ms=start_ms,
            reasoning_summary=(
                "No hard requirements specified for this role. "
                "All candidates pass Tier 1 pre-filter automatically."
            ),
            output_summary="No hard requirements — pre-filter passed",
            evidence_keys=[],
            model_used=None,
            cost_usd=0.0,
        )
        logger.info(
            "tier1_prefilter passed (no requirements)",
            node=node_name,
            candidate_id=candidate_id,
            duration_ms=trajectory_entry.duration_ms,
        )
        return {
            "hard_rejected": False,
            "trajectory": [trajectory_entry],
            "total_cost_usd": 0.0,
        }

    # Check each requirement
    failed_requirement: str | None = None
    failure_reason: str | None = None

    for requirement in hard_requirements:
        satisfied, reason = _requirement_satisfied(requirement, candidate_profile)
        if not satisfied:
            failed_requirement = requirement
            failure_reason = reason
            break

    if failed_requirement is not None:
        # Hard reject — build decision and feedback now
        elapsed_ms = int((time.time() * 1000) - start_ms)
        decision = _build_hard_reject_decision(
            candidate_id=candidate_id,
            failed_requirement=failed_requirement,
            failure_reason=failure_reason or "No evidence found",
            processing_time_ms=elapsed_ms,
            cost_usd=0.0,
        )
        feedback = _build_hard_reject_feedback(
            candidate_id=candidate_id,
            failed_requirement=failed_requirement,
        )

        trajectory_entry = make_trajectory_entry(
            node=node_name,
            start_time_ms=start_ms,
            reasoning_summary=(
                f"Hard requirement check failed. "
                f"Checked {len(hard_requirements)} requirement(s). "
                f"Failed on: '{failed_requirement}'. "
                f"Reason: {failure_reason}. "
                f"Pipeline short-circuited — no further analysis."
            ),
            output_summary=(
                f"HARD REJECT — failed requirement: '{failed_requirement}'"
            ),
            evidence_keys=[f"hard_req:{failed_requirement}"],
            model_used=None,
            cost_usd=0.0,
        )

        logger.info(
            "tier1_prefilter HARD REJECT",
            node=node_name,
            candidate_id=candidate_id,
            verdict="STRONG_NO",
            duration_ms=trajectory_entry.duration_ms,
        )

        return {
            "hard_rejected": True,
            "decision": decision,
            "candidate_feedback": feedback,
            "trajectory": [trajectory_entry],
            "total_cost_usd": 0.0,
        }

    # All requirements satisfied
    trajectory_entry = make_trajectory_entry(
        node=node_name,
        start_time_ms=start_ms,
        reasoning_summary=(
            f"All {len(hard_requirements)} hard requirement(s) satisfied. "
            f"Candidate passes Tier 1 pre-filter and proceeds to evidence extraction."
        ),
        output_summary=f"Pre-filter PASSED — {len(hard_requirements)} requirement(s) checked",
        evidence_keys=[f"hard_req:{r}" for r in hard_requirements],
        model_used=None,
        cost_usd=0.0,
    )

    logger.info(
        "tier1_prefilter passed",
        node=node_name,
        candidate_id=candidate_id,
        num_requirements_checked=len(hard_requirements),
        duration_ms=trajectory_entry.duration_ms,
    )

    return {
        "hard_rejected": False,
        "trajectory": [trajectory_entry],
        "total_cost_usd": 0.0,
    }
