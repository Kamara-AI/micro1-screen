"""
WHY: The LangGraph state is the shared memory of the pipeline. Every node
reads from it and writes partial updates back to it. The TypedDict definition
here is the contract for what can flow between nodes.

HOW: LangGraph uses TypedDict for state because it enables partial updates —
each node returns only the fields it changed, not the full state. This keeps
nodes decoupled and their output testable in isolation.

All fields are Optional because LangGraph initialises the state with just
the input and each node populates its own output field. A node that reads
a field should always check it is not None first (StateTransitionError if it is).
"""

import operator
from typing import Annotated, Optional, TypedDict

from screen.schemas.analysis import FitAnalysis
from screen.schemas.candidate import CandidateProfile
from screen.schemas.cohort import CohortAnalysis
from screen.schemas.decision import CandidateFeedback, Decision, HumanBrief
from screen.schemas.evidence import EvidenceBundle
from screen.schemas.input import ScreeningInput
from screen.schemas.trajectory import TrajectoryEntry


class ScreeningState(TypedDict):
    """
    WHY: The single source of truth as a candidate moves through the pipeline.
    Fields are populated sequentially by nodes; never overwritten once set
    (except trajectory, which is append-only).

    trajectory uses Annotated[list, operator.add] — LangGraph's built-in
    mechanism for append-only list fields. Each node appends one entry;
    no node replaces the list.

    total_cost_usd accumulates across nodes using the same mechanism.

    HOW: To initialise a run, create a ScreeningState with only
    `screening_input` set. All other fields default to None and are
    populated as the graph executes.
    """

    # ── Input (immutable after entry) ─────────────────────────────────────────
    screening_input: ScreeningInput

    # ── Pipeline node outputs (set once, never overwritten) ───────────────────
    candidate_profile: Optional[CandidateProfile]
    evidence_bundle: Optional[EvidenceBundle]
    fit_analysis: Optional[FitAnalysis]
    decision: Optional[Decision]
    human_brief: Optional[HumanBrief]
    candidate_feedback: Optional[CandidateFeedback]
    cohort_analysis: Optional[CohortAnalysis]

    # ── Routing flags (set by nodes, read by conditional edges) ───────────────
    hard_rejected: bool           # Set by tier1_prefilter — routes to END immediately
    should_escalate: bool         # Set by make_decision — routes to build_human_brief
    current_tier: int             # 1, 2, or 3 — set at entry, may update to 3 on escalation

    # ── Error state ───────────────────────────────────────────────────────────
    error_node: Optional[str]     # Set if a node raises an unrecoverable error
    error_message: Optional[str]

    # ── Audit trail (append-only — LangGraph reducer) ─────────────────────────
    # WHY: operator.add ensures that each node appends its TrajectoryEntry
    # without overwriting entries from prior nodes.
    trajectory: Annotated[list[TrajectoryEntry], operator.add]

    # ── Economics (accumulating — LangGraph reducer) ──────────────────────────
    # WHY: operator.add accumulates cost across all LLM calls in the pipeline.
    total_cost_usd: Annotated[float, operator.add]


def initial_state(screening_input: ScreeningInput) -> ScreeningState:
    """
    WHY: Every run starts from this clean initial state. Providing a constructor
    function prevents callers from accidentally omitting required fields or
    setting wrong defaults.

    HOW: Only screening_input is required. All optional fields are set to
    None or safe defaults. The graph entry point is always parse_candidate.
    """
    return ScreeningState(
        screening_input=screening_input,
        candidate_profile=None,
        evidence_bundle=None,
        fit_analysis=None,
        decision=None,
        human_brief=None,
        candidate_feedback=None,
        cohort_analysis=None,
        hard_rejected=False,
        should_escalate=False,
        current_tier=1,
        error_node=None,
        error_message=None,
        trajectory=[],
        total_cost_usd=0.0,
    )
