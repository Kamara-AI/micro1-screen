"""
WHY: The LangGraph graph assembles all nodes into the screening pipeline.
Conditional edges implement the routing logic — hard rejects short-circuit
to END, ESCALATE verdicts route to build_human_brief, batch mode adds comparative_rank.

HOW: StateGraph(ScreeningState) with add_node() for each node and
add_conditional_edges() for routing decisions. The compiled graph is
the callable that runs the full pipeline.

ROUTING LOGIC:
  parse_candidate → tier1_prefilter
  tier1_prefilter → conditional:
    hard_rejected=True → candidate_feedback → comparative_rank → END
    else → extract_evidence
  extract_evidence → analyze_fit → detect_bias → make_decision
  make_decision → conditional:
    should_escalate=True → build_human_brief → candidate_feedback → comparative_rank → END
    else → candidate_feedback → comparative_rank → END

WHY the routing terminates at comparative_rank: Every candidate (regardless of verdict
path) passes through comparative_rank as the final node. If batch_id is None, the
node returns immediately with a minimal trajectory entry. This keeps the graph topology
simple — one end node, two possible paths to reach it.

WHY compile() is called at module level: The compiled graph is the callable used
by the runner. Compiling once at import time is cheaper than compiling per request.
"""

from langgraph.graph import END, StateGraph

from screen.schemas.state import ScreeningState

from screen.agent.nodes.parse_candidate import parse_candidate_node
from screen.agent.nodes.tier1_prefilter import tier1_prefilter_node
from screen.agent.nodes.extract_evidence import extract_evidence_node
from screen.agent.nodes.analyze_fit import analyze_fit_node
from screen.agent.nodes.detect_bias import detect_bias_node
from screen.agent.nodes.make_decision import make_decision_node
from screen.agent.nodes.build_human_brief import build_human_brief_node
from screen.agent.nodes.candidate_feedback import candidate_feedback_node
from screen.agent.nodes.comparative_rank import comparative_rank_node


# ── Routing functions ──────────────────────────────────────────────────────────
# WHY: Routing functions are pure state readers — they take state and return
# the name of the next node. This keeps routing logic readable and testable
# independently of node logic.

def _route_after_prefilter(state: ScreeningState) -> str:
    """
    WHY: Hard-rejected candidates skip the entire analysis pipeline.
    Their decision and feedback were already built by tier1_prefilter.
    They go directly to comparative_rank (which handles batch_id=None gracefully).
    """
    if state.get("hard_rejected", False):
        return "candidate_feedback"
    return "extract_evidence"


def _route_after_decision(state: ScreeningState) -> str:
    """
    WHY: ESCALATE verdicts need a human brief before feedback is generated.
    Non-escalate verdicts go directly to candidate_feedback.

    The should_escalate flag is set by make_decision_node — we trust it here.
    """
    if state.get("should_escalate", False):
        return "build_human_brief"
    return "candidate_feedback"


# ── Graph construction ─────────────────────────────────────────────────────────

def _build_screening_graph() -> StateGraph:
    """
    WHY: Isolated constructor so the graph can be rebuilt for testing
    without affecting the module-level compiled graph.

    HOW: Registers all nodes, then wires edges in pipeline order.
    Conditional edges implement the routing functions above.
    """
    graph = StateGraph(ScreeningState)

    # ── Register nodes ─────────────────────────────────────────────────────────
    graph.add_node("parse_candidate", parse_candidate_node)
    graph.add_node("tier1_prefilter", tier1_prefilter_node)
    graph.add_node("extract_evidence", extract_evidence_node)
    graph.add_node("analyze_fit", analyze_fit_node)
    graph.add_node("detect_bias", detect_bias_node)
    graph.add_node("make_decision", make_decision_node)
    graph.add_node("build_human_brief", build_human_brief_node)
    graph.add_node("candidate_feedback", candidate_feedback_node)
    graph.add_node("comparative_rank", comparative_rank_node)

    # ── Entry point ────────────────────────────────────────────────────────────
    graph.set_entry_point("parse_candidate")

    # ── Linear edges ──────────────────────────────────────────────────────────
    graph.add_edge("parse_candidate", "tier1_prefilter")

    # ── Conditional: after prefilter ──────────────────────────────────────────
    graph.add_conditional_edges(
        "tier1_prefilter",
        _route_after_prefilter,
        {
            "candidate_feedback": "candidate_feedback",  # Hard reject path
            "extract_evidence": "extract_evidence",       # Main analysis path
        },
    )

    # ── Linear: main analysis chain ───────────────────────────────────────────
    graph.add_edge("extract_evidence", "analyze_fit")
    graph.add_edge("analyze_fit", "detect_bias")
    graph.add_edge("detect_bias", "make_decision")

    # ── Conditional: after decision ───────────────────────────────────────────
    graph.add_conditional_edges(
        "make_decision",
        _route_after_decision,
        {
            "build_human_brief": "build_human_brief",   # ESCALATE path
            "candidate_feedback": "candidate_feedback",  # Standard path
        },
    )

    # ── Escalation path: brief → feedback ─────────────────────────────────────
    graph.add_edge("build_human_brief", "candidate_feedback")

    # ── All paths converge at comparative_rank → END ──────────────────────────
    graph.add_edge("candidate_feedback", "comparative_rank")
    graph.add_edge("comparative_rank", END)

    return graph


# ── Compile the graph ──────────────────────────────────────────────────────────
# WHY: Compile once at module load. The compiled graph validates the schema
# and edge wiring. If there's a structural bug (missing node, invalid edge),
# it surfaces here at import time — not at runtime when a candidate is being evaluated.
_raw_graph = _build_screening_graph()
screening_graph = _raw_graph.compile()

__all__ = ["screening_graph"]
