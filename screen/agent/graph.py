"""
WHY: The LangGraph graph assembles all nodes into the screening pipeline.
Conditional edges implement the routing logic — hard rejects short-circuit
to END, ESCALATE verdicts route to build_human_brief, batch mode adds comparative_rank.

HOW: StateGraph(ScreeningState) with add_node() for each node and
add_conditional_edges() for routing decisions. The compiled graph is
the callable that runs the full pipeline.

ROUTING LOGIC:
  structural_precheck → conditional:
    hard_rejected=True → comparative_rank → END  (0 LLM calls — explicit contradiction)
    else → parse_candidate
  parse_candidate → tier1_prefilter
  tier1_prefilter → conditional:
    hard_rejected=True → candidate_feedback → comparative_rank → END
    else → extract_evidence
  extract_evidence → verify_claims → analyze_fit → detect_bias → make_decision
  make_decision → conditional:
    should_escalate=True → build_human_brief → candidate_feedback → comparative_rank → END
    else → candidate_feedback → comparative_rank → END

WHY structural_precheck is the entry point: It runs before any LLM call and catches
only explicit self-contradictions (e.g., "I have 2 years of experience" + "minimum 10
years required"). This is NOT keyword matching — it fires only when the candidate's
own stated facts make the role impossible. It saves the parse_candidate Flash call and
the candidate_feedback Flash call for structurally impossible applications.

WHY the routing terminates at comparative_rank: Every candidate (regardless of verdict
path) passes through comparative_rank as the final node. If batch_id is None, the
node returns immediately with a minimal trajectory entry. This keeps the graph topology
simple — one end node, multiple possible paths to reach it.

WHY compile() is called at module level: The compiled graph is the callable used
by the runner. Compiling once at import time is cheaper than compiling per request.
"""

from langgraph.graph import END, StateGraph

from screen.schemas.state import ScreeningState

from screen.agent.nodes.structural_precheck import structural_precheck_node
from screen.agent.nodes.parse_candidate import parse_candidate_node
from screen.agent.nodes.tier1_prefilter import tier1_prefilter_node
from screen.agent.nodes.extract_evidence import extract_evidence_node
from screen.agent.nodes.verify_claims import verify_claims_node
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

def _route_after_structural_precheck(state: ScreeningState) -> str:
    """
    WHY: If structural_precheck found an explicit contradiction, the Decision
    and CandidateFeedback are already built — skip straight to comparative_rank.
    This saves parse_candidate (Flash) + candidate_feedback (Flash) LLM calls.
    """
    if state.get("hard_rejected", False):
        return "comparative_rank"
    return "parse_candidate"


def _route_after_prefilter(state: ScreeningState) -> str:
    """
    WHY: Hard-rejected candidates skip the entire analysis pipeline.
    Their decision and feedback were already built by tier1_prefilter.
    They go directly to candidate_feedback (which uses the LLM to personalise
    the rejection message against the structured profile).
    """
    if state.get("hard_rejected", False):
        return "generate_feedback"
    return "extract_evidence"


def _route_after_decision(state: ScreeningState) -> str:
    """
    WHY: ESCALATE verdicts need a human brief before feedback is generated.
    Non-escalate verdicts go directly to generate_feedback.

    The should_escalate flag is set by make_decision_node — we trust it here.
    """
    if state.get("should_escalate", False):
        return "build_human_brief"
    return "generate_feedback"


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
    graph.add_node("structural_precheck", structural_precheck_node)
    graph.add_node("parse_candidate", parse_candidate_node)
    graph.add_node("tier1_prefilter", tier1_prefilter_node)
    graph.add_node("extract_evidence", extract_evidence_node)
    graph.add_node("verify_claims", verify_claims_node)
    graph.add_node("analyze_fit", analyze_fit_node)
    graph.add_node("detect_bias", detect_bias_node)
    graph.add_node("make_decision", make_decision_node)
    graph.add_node("build_human_brief", build_human_brief_node)
    graph.add_node("generate_feedback", candidate_feedback_node)
    graph.add_node("comparative_rank", comparative_rank_node)

    # ── Entry point ────────────────────────────────────────────────────────────
    graph.set_entry_point("structural_precheck")

    # ── Conditional: after structural precheck ────────────────────────────────
    graph.add_conditional_edges(
        "structural_precheck",
        _route_after_structural_precheck,
        {
            "comparative_rank": "comparative_rank",  # Explicit contradiction path
            "parse_candidate": "parse_candidate",    # Normal pipeline path
        },
    )

    # ── Linear edges ──────────────────────────────────────────────────────────
    graph.add_edge("parse_candidate", "tier1_prefilter")

    # ── Conditional: after prefilter ──────────────────────────────────────────
    graph.add_conditional_edges(
        "tier1_prefilter",
        _route_after_prefilter,
        {
            "generate_feedback": "generate_feedback",  # Hard reject path
            "extract_evidence": "extract_evidence",    # Main analysis path
        },
    )

    # ── Linear: main analysis chain ───────────────────────────────────────────
    # WHY: verify_claims sits between extract_evidence and analyze_fit.
    # It upgrades B→A claims via GitHub/web/portfolio before fit scoring runs,
    # so analyze_fit sees externally-confirmed evidence, not just LLM-inferred tiers.
    graph.add_edge("extract_evidence", "verify_claims")
    graph.add_edge("verify_claims", "analyze_fit")
    graph.add_edge("analyze_fit", "detect_bias")
    graph.add_edge("detect_bias", "make_decision")

    # ── Conditional: after decision ───────────────────────────────────────────
    graph.add_conditional_edges(
        "make_decision",
        _route_after_decision,
        {
            "build_human_brief": "build_human_brief",  # ESCALATE path
            "generate_feedback": "generate_feedback",  # Standard path
        },
    )

    # ── Escalation path: brief → feedback ─────────────────────────────────────
    graph.add_edge("build_human_brief", "generate_feedback")

    # ── All paths converge at comparative_rank → END ──────────────────────────
    graph.add_edge("generate_feedback", "comparative_rank")
    graph.add_edge("comparative_rank", END)

    return graph


# ── Compile the graph ──────────────────────────────────────────────────────────
# WHY: Compile once at module load. The compiled graph validates the schema
# and edge wiring. If there's a structural bug (missing node, invalid edge),
# it surfaces here at import time — not at runtime when a candidate is being evaluated.
_raw_graph = _build_screening_graph()
screening_graph = _raw_graph.compile()

__all__ = ["screening_graph"]
