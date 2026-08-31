"""
WHY: Node 2 — the deterministic gatekeeper. No LLM call here. Hard requirements
are binary: either the candidate satisfies them or they don't. Using an LLM for
this would introduce hallucination risk on the highest-stakes check in the pipeline.

Hard requirements are knockout criteria set by the hiring team — e.g., "right to
work in UK", "minimum 5 years Python", "must have active CPA". A candidate who
fails any one of these cannot proceed regardless of how strong their profile is.

HOW: The node reads hard_requirements from ScreeningInput and checks each one
against the candidate's skills_stated and role descriptions. The matching is
heuristic (substring + keyword + year comparison) — more sophisticated matching
can be layered on later. A single failure triggers hard_rejected=True and a
STRONG_NO Decision.

YEAR REQUIREMENTS: Requirements like "minimum 5 years" are NOT checked via keyword
match — they are checked numerically against CandidateProfile.total_years_experience.
If total_years_experience is None (parse_candidate couldn't calculate from dates),
the year requirement is treated as satisfied so the candidate gets full LLM analysis.
The structural_precheck node (which runs before parse_candidate) handles the case
where the candidate's OWN stated years contradict the requirement.
"""

import re
import time
from typing import Any

# WHY: Same patterns as structural_precheck — detect minimum year requirements.
# These are applied NUMERICALLY against total_years_experience from the parsed profile.
_REQUIRED_YEARS_PATTERNS = [
    re.compile(r"minimum\s+\d+\+?\s+years?", re.IGNORECASE),
    re.compile(r"at\s+least\s+\d+\+?\s+years?", re.IGNORECASE),
    re.compile(r"\d+\+\s+years?", re.IGNORECASE),            # "5+ years"
    re.compile(r"\d+\+?\s+years?\s+(?:minimum|required)", re.IGNORECASE),
]
_REQUIRED_YEARS_WITH_CAPTURE = [
    re.compile(r"minimum\s+(\d+)\+?\s+years?", re.IGNORECASE),
    re.compile(r"at\s+least\s+(\d+)\+?\s+years?", re.IGNORECASE),
    re.compile(r"(\d+)\+\s+years?", re.IGNORECASE),
    re.compile(r"(\d+)\+?\s+years?\s+(?:minimum|required)", re.IGNORECASE),
]

# WHY: 1-year buffer mirrors structural_precheck. If the LLM calculated 4.2 years
# from CV dates and the requirement is 5, that's close enough for LLM reasoning.
# The prefilter is a hard gate for clear gaps, not a sub-year precision tool.
_YEAR_BUFFER = 1


def _extract_min_years(requirement: str) -> int | None:
    """Return the minimum years extracted from a requirement string, or None."""
    for pattern in _REQUIRED_YEARS_WITH_CAPTURE:
        match = pattern.search(requirement)
        if match:
            return int(match.group(1))
    return None


def _strip_year_phrases(requirement: str) -> str:
    """
    WHY: Requirements like "minimum 10 years java" have both a year threshold and
    a skill keyword. After the year check, we need to check the residual keyword
    ("java") separately. Stripping the year phrase extracts that residual.
    """
    stripped = requirement
    for pattern in _REQUIRED_YEARS_PATTERNS:
        stripped = pattern.sub("", stripped)
    # Also strip common qualifiers left behind ("of experience", "of", "in")
    stripped = re.sub(
        r"\b(?:of\s+experience|of\s+professional\s+experience|experience\s+in|in\s+the\s+field|of)\b",
        "",
        stripped,
        flags=re.IGNORECASE,
    )
    return stripped.strip(" ,;")  # Remove trailing punctuation/whitespace

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

    HOW:
    1. If requirement contains a minimum year threshold: check numerically against
       total_years_experience. Pass through (True) if experience data is absent —
       LLM analysis should handle data gaps, not the prefilter.
    2. Otherwise: keyword substring match against skills_stated, role titles,
       role achievements, and education fields.

    Returns (satisfied: bool, reason: str) so callers know WHY a requirement failed.
    """
    # ── Year-based requirements: numeric check, then residual keyword check ───
    # WHY: "Minimum 5 years of professional experience" will NEVER appear as a
    # skill or role title — substring matching would always falsely reject here.
    # "Minimum 10 years java" is compound: year threshold + skill. We check both:
    # 1. Year threshold numerically against total_years_experience.
    # 2. Residual keyword (e.g. "java") via the normal substring check below.
    min_years = _extract_min_years(requirement)
    if min_years is not None:
        # ── Check year threshold ──────────────────────────────────────────────
        if candidate_profile.total_years_experience is not None:
            if candidate_profile.total_years_experience < (min_years - _YEAR_BUFFER):
                return False, (
                    f"Year requirement not met: {candidate_profile.total_years_experience:.1f} years "
                    f"< {min_years} years minimum"
                )
        # Year check passed (or no experience data — let LLM reason about it).
        # Now check residual keyword if any remains after stripping the year phrase.
        residual = _strip_year_phrases(requirement)
        if not residual:
            # Purely year-based requirement — year check above is the only gate.
            return True, (
                f"Year requirement: {'met' if candidate_profile.total_years_experience is not None else 'unverifiable — passing to LLM'}"
            )
        # Fall through to keyword check with residual (e.g. "java" from "minimum 10 years java")
        requirement = residual  # Replace requirement with residual for keyword matching below

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
