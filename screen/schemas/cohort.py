"""
WHY: Cohort analysis is the feature no ATS or AI screener provides. When
screening a batch of candidates for the same role, the agent doesn't just
produce individual verdicts — it also ranks candidates comparatively across
dimensions and surfaces cohort-level patterns.

This answers the question every hiring manager actually asks: "Of all the
people we screened, who is the best fit, and why?"

HOW: The comparative_rank node runs after all individual candidates are
processed. It reads all Decision and FitAnalysis objects for a batch_id
and produces a CohortAnalysis.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CandidateRank(BaseModel):
    """
    WHY: Per-candidate ranking within the cohort. Multiple rank dimensions
    prevent a single strong signal from hiding a critical weakness.

    A candidate ranked 1st on technical_rank but 8th on learning_velocity_rank
    is a very different hire from one ranked 3rd on both.
    """

    model_config = ConfigDict(frozen=True)

    candidate_id: str
    verdict: str = Field(..., description="Individual verdict for quick reference")
    confidence_pct: float

    # Dimension ranks (1 = best in cohort)
    overall_rank: int = Field(..., ge=1, description="Composite rank across all dimensions")
    technical_rank: int = Field(..., ge=1)
    velocity_rank: int = Field(..., ge=1, description="Learning velocity rank")
    trajectory_rank: int = Field(..., ge=1, description="Career trajectory/shape rank")
    builder_rank: int = Field(..., ge=1, description="Builder signal strength rank")

    standout_signal: str = Field(
        ...,
        description=(
            "The one thing about this candidate that stands out from the cohort — "
            "positive or negative. E.g. 'Only candidate with verified open source contributions'"
        ),
    )


class CohortAnalysis(BaseModel):
    """
    WHY: The cohort view gives the hiring manager strategic intelligence:
    not just 'who passed' but 'who is the best fit and in what dimension'.

    cohort_bias_flags is a batch-level check — if 80% of rejections are
    from candidates whose CVs mention certain universities, we flag it.
    This is the continuous bias monitoring that no other tool does natively.

    HOW: Populated by the comparative_rank node only when batch_id is present
    and ≥2 candidates have been processed with that batch_id.
    """

    model_config = ConfigDict(frozen=True)

    batch_id: str
    total_candidates: int = Field(..., ge=2)
    rankings: list[CandidateRank] = Field(
        ...,
        description="All candidates ranked, ordered by overall_rank ascending (1 = best)",
    )

    # ── Top performers by dimension ───────────────────────────────────────────
    best_overall_id: str = Field(..., description="candidate_id of top-ranked candidate")
    best_technical_id: str
    best_velocity_id: str
    best_trajectory_id: str

    # ── Summary for hiring manager ────────────────────────────────────────────
    recommended_for_interview: list[str] = Field(
        ...,
        description="candidate_ids with YES or STRONG_YES verdicts, ordered by overall_rank",
    )
    escalated_candidates: list[str] = Field(
        default_factory=list,
        description="candidate_ids with ESCALATE verdicts — need human verification before decision",
    )
    clear_rejections: list[str] = Field(
        default_factory=list,
        description="candidate_ids with NO or STRONG_NO verdicts",
    )

    # ── Cohort-level bias monitoring ──────────────────────────────────────────
    cohort_bias_flags: list[str] = Field(
        default_factory=list,
        description=(
            "Batch-level patterns that may indicate systematic bias. "
            "E.g. 'All 4 rejected candidates attended non-prestige universities — "
            "verify prestige bias is not driving rejections'"
        ),
    )

    # ── Economics ─────────────────────────────────────────────────────────────
    total_cost_usd: float = Field(..., description="Total LLM API cost for this batch")
    cost_per_candidate_usd: float = Field(..., description="Average cost per candidate")
    total_processing_time_ms: int

    # ── Notable patterns ──────────────────────────────────────────────────────
    cohort_insight: Optional[str] = Field(
        default=None,
        description=(
            "One-paragraph insight about the cohort quality and what it means for the search. "
            "E.g. 'Strong cohort on technical depth, weak on leadership trajectory — "
            "consider whether this role truly requires management experience or if individual "
            "contributor excellence is sufficient'"
        ),
    )
