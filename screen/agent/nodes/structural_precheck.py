"""
WHY: Node 0 — runs BEFORE parse_candidate. Catches structurally impossible
applications without spending any LLM tokens.

This is NOT an ATS keyword filter. The distinction is critical:
  ATS rejects on ABSENCE — "Python not mentioned → reject."
  SCREEN precheck rejects on EXPLICIT CONTRADICTION — "candidate states 2 years,
  role requires minimum 10 years → the candidate's own words make this impossible."

A nurse applying to a health tech role is not caught here. Their CV has no explicit
year contradiction against the requirement. The full pipeline runs and the LLM
reasons about transferable domain knowledge. That's the right behaviour.

A candidate who writes "I have 1 year of total professional experience" applying
to a role requiring "minimum 8 years" IS caught here. No LLM reasoning changes a
directly stated fact. The precheck makes this determination in <5ms with zero API cost.

HOW:
1. Extract explicit year-of-experience statements from raw cv_text using regex.
   Only fires on direct statements: "N years of experience", "N years in the field",
   etc. Does not infer from dates (that requires LLM reasoning in parse_candidate).
2. Extract minimum year requirements from hard_requirements strings.
3. If stated years < required years - 1 (1-year buffer for rounding), hard reject.
   The buffer prevents rejecting "4 years" against "minimum 5 years" — close enough
   that the LLM should reason, not the regex.
4. Build a full Decision + CandidateFeedback so the graph can route directly to
   comparative_rank without running parse_candidate or candidate_feedback.

COST SAVING: A structurally impossible CV currently costs 2 Flash LLM calls:
parse_candidate (extract structure) + candidate_feedback (generate feedback text).
With this node, both are skipped. At scale, early rejection is the highest-ROI
cost optimisation — paying LLM cost to reason about an impossible application is waste.

GRAPH ROUTING:
  hard_rejected=True  → comparative_rank (Decision + Feedback already built)
  hard_rejected=False → parse_candidate (normal pipeline)
"""

import re
import time
from typing import Any

from screen.core.exceptions import StateTransitionError
from screen.core.logging_config import get_logger
from screen.core.trajectory import make_trajectory_entry
from screen.schemas.decision import CandidateFeedback, Decision
from screen.schemas.input import ScreeningInput
from screen.schemas.state import ScreeningState

logger = get_logger(__name__)

# ── Regex patterns ─────────────────────────────────────────────────────────────
# WHY: Only match explicit self-statements about total experience. Do not match
# "5 years at Company X" — that's a role duration, not total experience claimed.
_STATED_YEARS_PATTERNS = [
    re.compile(
        r"(?:i\s+have|with|gained|brings?|offering)\s+(\d+)\+?\s+years?\s+"
        r"(?:of\s+)?(?:total\s+)?(?:professional\s+)?experience",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\d+)\+?\s+years?\s+(?:of\s+)?(?:professional\s+)?experience\s+in\s+(?:the\s+)?(?:field|industry)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:total|overall)\s+(?:of\s+)?(\d+)\+?\s+years?\s+(?:of\s+)?(?:professional\s+)?experience",
        re.IGNORECASE,
    ),
]

# WHY: Match minimum year requirements in plain-English hard requirement strings.
_REQUIRED_YEARS_PATTERNS = [
    re.compile(r"minimum\s+(\d+)\+?\s+years?", re.IGNORECASE),
    re.compile(r"at\s+least\s+(\d+)\+?\s+years?", re.IGNORECASE),
    re.compile(r"(\d+)\+\s+years?", re.IGNORECASE),           # "5+ years"
    re.compile(r"(\d+)\+?\s+years?\s+(?:minimum|required)", re.IGNORECASE),
]

# WHY: 1-year buffer prevents rejecting "4 years" against "5 years minimum".
# A candidate who writes "4 years" might have 4.8 years — LLM should reason.
# We only short-circuit on clear gaps (2 years vs 10 year requirement).
_YEAR_BUFFER = 1


def _extract_stated_years(cv_text: str) -> int | None:
    """
    Extract an explicitly stated total years of experience from raw CV text.

    WHY: Only explicit total-experience statements are safe to act on without
    LLM reasoning. Role-specific durations ("3 years at Company X") are not
    extracted here — those require context the LLM provides.

    Args:
        cv_text: Raw CV text from ScreeningInput.

    Returns:
        Integer years if an explicit statement is found, else None.
    """
    for pattern in _STATED_YEARS_PATTERNS:
        match = pattern.search(cv_text)
        if match:
            return int(match.group(1))
    return None


def _extract_min_years_required(requirements: list[str]) -> tuple[int, str] | None:
    """
    Scan hard requirements for a minimum years of experience criterion.

    Args:
        requirements: List of hard requirement strings from ScreeningInput.

    Returns:
        (min_years, requirement_string) if found, else None.
    """
    for req in requirements:
        for pattern in _REQUIRED_YEARS_PATTERNS:
            match = pattern.search(req)
            if match:
                return int(match.group(1)), req
    return None


def structural_precheck_node(state: ScreeningState) -> dict[str, Any]:
    """
    WHY: Zero-cost gate before the first LLM call. Rejects only on explicit
    candidate self-statements that directly contradict a hard requirement.

    HOW: Reads screening_input directly from state (parse_candidate hasn't run yet).
    Extracts explicit year statements from raw cv_text and minimum year requirements
    from hard_requirements. If stated < required - buffer, builds a hard-reject
    Decision + Feedback and sets hard_rejected=True.

    Args:
        state: ScreeningState — only screening_input is populated at this stage.

    Returns:
        State update dict. If hard_rejected=True, includes Decision and Feedback.
        If hard_rejected=False, passes through cleanly.
    """
    node_name = "structural_precheck"
    start_ms = time.time() * 1000

    screening_input: ScreeningInput | None = state.get("screening_input")
    if screening_input is None:
        raise StateTransitionError(node_name, "screening_input")

    candidate_id = screening_input.candidate_id
    cv_text = screening_input.cv_text
    hard_requirements = screening_input.hard_requirements

    logger.info(
        "structural_precheck started",
        node=node_name,
        candidate_id=candidate_id,
        num_requirements=len(hard_requirements),
    )

    # ── Check 1: explicit year contradiction ──────────────────────────────────
    # Only run if there is at least one year-based hard requirement
    year_requirement = _extract_min_years_required(hard_requirements)

    if year_requirement is not None:
        required_years, req_string = year_requirement
        stated_years = _extract_stated_years(cv_text)

        if stated_years is not None and stated_years < (required_years - _YEAR_BUFFER):
            # Explicit contradiction found — hard reject without LLM
            elapsed_ms = int((time.time() * 1000) - start_ms)

            reasoning = (
                f"Structural precheck: candidate explicitly states {stated_years} year(s) "
                f"of experience. Hard requirement: '{req_string}' (minimum {required_years} years). "
                f"Gap of {required_years - stated_years} year(s) exceeds the {_YEAR_BUFFER}-year "
                f"buffer. This is an explicit self-contradiction — no LLM inference required. "
                f"parse_candidate and candidate_feedback LLM calls skipped."
            )

            decision = Decision(
                candidate_id=candidate_id,
                verdict="STRONG_NO",
                confidence_pct=100.0,
                primary_evidence=[
                    f"Structural precheck: candidate states {stated_years} year(s) of experience",
                    f"Hard requirement not met: '{req_string}'",
                    f"Gap: {required_years - stated_years} year(s) below minimum — explicit self-contradiction",
                    "No LLM calls made — deterministic rejection on stated facts only",
                ],
                escalation_reason=None,
                escalation_category=None,
                tier_processed=0,  # Pre-parse tier
                estimated_cost_usd=0.0,
                processing_time_ms=elapsed_ms,
                passed_hard_requirements=False,
            )

            feedback = CandidateFeedback(
                candidate_id=candidate_id,
                verdict_communicated="not selected for this role at this time",
                genuine_strength=(
                    "Your application was considered and your background reviewed. "
                    "We recognise the professional experience you have built."
                ),
                gap_for_this_role=(
                    f"This role requires a minimum of {required_years} years of experience. "
                    f"Based on your application, you currently have {stated_years} year(s). "
                    f"This is a non-negotiable criterion for this position."
                ),
                encouragement=(
                    f"We encourage you to apply again once you have reached the "
                    f"{required_years}-year experience threshold. Your application will "
                    f"be given full consideration at that point."
                ),
            )

            trajectory_entry = make_trajectory_entry(
                node=node_name,
                start_time_ms=start_ms,
                reasoning_summary=reasoning,
                output_summary=(
                    f"STRUCTURAL REJECT — stated {stated_years}yr vs required {required_years}yr "
                    f"— 0 LLM calls"
                ),
                evidence_keys=[f"structural_contradiction:years_{stated_years}_vs_{required_years}"],
                model_used=None,
                cost_usd=0.0,
            )

            logger.info(
                "structural_precheck HARD REJECT",
                node=node_name,
                candidate_id=candidate_id,
                stated_years=stated_years,
                required_years=required_years,
                duration_ms=trajectory_entry.duration_ms,
            )

            return {
                "hard_rejected": True,
                "decision": decision,
                "candidate_feedback": feedback,
                "trajectory": [trajectory_entry],
                "total_cost_usd": 0.0,
            }

    # ── No structural impossibility found — pass to full pipeline ─────────────
    trajectory_entry = make_trajectory_entry(
        node=node_name,
        start_time_ms=start_ms,
        reasoning_summary=(
            "Structural precheck passed. No explicit year contradiction found in raw CV text. "
            "Candidate proceeds to full pipeline — parse_candidate will extract structured profile "
            "for deterministic tier1_prefilter check."
        ),
        output_summary="Structural precheck PASSED — proceeding to parse_candidate",
        evidence_keys=[],
        model_used=None,
        cost_usd=0.0,
    )

    logger.info(
        "structural_precheck passed",
        node=node_name,
        candidate_id=candidate_id,
        duration_ms=trajectory_entry.duration_ms,
    )

    return {
        "hard_rejected": False,
        "trajectory": [trajectory_entry],
        "total_cost_usd": 0.0,
    }
