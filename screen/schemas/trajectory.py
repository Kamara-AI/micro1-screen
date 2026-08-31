"""
WHY: The trajectory IS the product. For the micro1 hackathon, judges need to
see the agent think — not just the verdict. TrajectoryEntry captures every
node's reasoning, timing, and cost so the full pipeline is auditable.

This also implements the EU AI Act "high-risk AI" documentation requirement:
every automated employment decision must have an audit trail that shows
what information was used, what model made the call, and what the reasoning was.

HOW: Every node calls log_trajectory() as its last action before returning state.
The trajectory list grows append-only through the pipeline.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TrajectoryEntry(BaseModel):
    """
    WHY: One entry per node execution. The sequence of entries tells the full
    story of how the pipeline arrived at its verdict.

    reasoning_summary is a plain-English explanation of what this node did and
    why — written to be readable by a hiring manager, not just a developer.

    evidence_keys lists the specific claim/flag IDs that this node used, so a
    reviewer can cross-reference against the EvidenceBundle without re-reading
    the full log.

    PRIVACY: reasoning_summary must never contain raw CV text, candidate names,
    or any PII. It summarises what was found without reproducing what was said.
    """

    model_config = ConfigDict(frozen=True)

    node: str = Field(..., description="Node name — e.g. 'extract_evidence', 'make_decision'")
    timestamp_eat: str = Field(
        ...,
        description="ISO timestamp in East Africa Time (UTC+3) — project timezone standard",
    )
    reasoning_summary: str = Field(
        ...,
        description=(
            "Plain-English explanation of what this node found and decided. "
            "Written for a hiring manager, not a developer. No raw CV text."
        ),
    )
    evidence_keys: list[str] = Field(
        default_factory=list,
        description="Identifiers of claims/flags/contradictions this node used or produced",
    )
    model_used: Optional[str] = Field(
        default=None,
        description="LLM model ID if this node made an LLM call. None for deterministic nodes.",
    )
    duration_ms: int = Field(..., ge=0, description="Node execution time in milliseconds")
    cost_usd: float = Field(..., ge=0.0, description="Estimated LLM API cost for this node")
    output_summary: str = Field(
        ...,
        description="One-line summary of what this node produced. E.g. '12 claims extracted, 1 critical contradiction'",
    )


class HumanOverride(BaseModel):
    """
    WHY: Human override records close the feedback loop. When a human reviewer
    disagrees with the agent's verdict, recording the override with a reason
    builds the correction dataset that improves calibration over time.

    This implements the "calibration loop" mental model from our research —
    the agent learns which types of candidates it systematically misclassifies.

    HOW: The evaluation runner writes HumanOverride records. In production,
    this would be submitted by the recruiter through a review interface.
    outcome is populated later when the hire's performance is known.
    """

    model_config = ConfigDict(frozen=True)

    candidate_id: str
    batch_id: Optional[str] = None
    agent_verdict: str
    human_verdict: str
    override_reason: str = Field(
        ...,
        description=(
            "Why the human disagreed. E.g. 'Agent missed that bootcamp + 3 shipped products "
            "outweighs CS degree for this startup role'"
        ),
    )
    timestamp_eat: str
    outcome: Optional[str] = Field(
        default=None,
        description=(
            "Populated when known: 'hired_strong_performer', 'hired_poor_performer', "
            "'rejected_at_offer', 'withdrew'. This is the ground truth for calibration."
        ),
    )
