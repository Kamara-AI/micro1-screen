"""
WHY: All API-layer request/response Pydantic models live here, separate from
the screen package's internal schemas. This boundary means the API contract
can evolve independently from the internal pipeline schemas.

HOW: All models use Pydantic v2. Response models are strict — no Optional
fields that aren't genuinely optional at the API boundary. Request models
mirror ScreeningInput but are not the same object — they go through explicit
mapping in route handlers so API changes don't silently break internal logic.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request models ────────────────────────────────────────────────────────────


class ScreenRequest(BaseModel):
    """
    WHY: Maps to ScreeningInput. Defined separately so the API can enforce
    its own validation rules and evolve independently from the internal schema.
    """

    candidate_id: str = Field(..., description="Unique identifier for the candidate")
    role_seniority: str = Field(
        ...,
        description="junior | mid | senior | lead",
        pattern="^(junior|mid|senior|lead)$",
    )
    role_type: str = Field(
        ...,
        description="engineering | data_science | operations | other",
        pattern="^(engineering|data_science|operations|other)$",
    )
    cv_text: str = Field(..., min_length=50, description="Full CV text")
    job_description: str = Field(..., min_length=50, description="Full job description text")
    hard_requirements: list[str] = Field(
        ..., min_length=1, description="Non-negotiable requirements — any miss = STRONG_NO"
    )
    batch_id: Optional[str] = Field(default=None, description="Groups candidates for comparative ranking")


class BatchScreenRequest(BaseModel):
    """Request body for POST /api/v1/batch."""

    candidates: list[ScreenRequest] = Field(..., min_length=1)


class OverrideRequest(BaseModel):
    """
    WHY: A human reviewer may override the agent's verdict after reviewing
    the HumanBrief. Both the new verdict and a mandatory reason are required —
    overrides without documented reasoning are not accepted.
    """

    override_verdict: str = Field(
        ...,
        description="Reviewer-assigned verdict: STRONG_YES | YES | AMBIGUOUS | NO | STRONG_NO",
        pattern="^(STRONG_YES|YES|AMBIGUOUS|NO|STRONG_NO)$",
    )
    reason: str = Field(
        ...,
        min_length=10,
        description="Why the reviewer overrides the agent. Mandatory — not accepting blank overrides.",
    )


class OutcomeRequest(BaseModel):
    """
    WHY: Outcome data (was the candidate hired? how did they perform?) feeds
    back into long-term calibration of confidence thresholds. Capturing it
    at the API layer makes SCREEN a learning system, not just a screening tool.
    """

    hired: bool = Field(..., description="True if the candidate was hired")
    performance_90d: Optional[str] = Field(
        default=None,
        description="90-day performance assessment: excellent | good | adequate | poor",
    )
    notes: Optional[str] = Field(default=None, description="Free-text recruiter notes")


# ── Response models ───────────────────────────────────────────────────────────


class CandidateFeedbackResponse(BaseModel):
    """Serialisable subset of CandidateFeedback for the API response."""

    genuine_strength: str
    gap_for_this_role: str
    encouragement: Optional[str] = None


class ScreenResponse(BaseModel):
    """
    WHY: One structured response per candidate. Fields are chosen to give the
    caller everything needed to render a recruiter-facing UI or trigger downstream
    workflow — without exposing internal pipeline state.

    primary_evidence carries the top 3 reasons (from Decision.primary_evidence)
    so callers don't have to fetch the full run to understand the verdict.
    """

    run_id: UUID
    candidate_id: str
    verdict: str
    confidence_pct: float
    cost_usd: float
    duration_ms: int
    ensemble_runs: int
    escalated: bool
    human_brief: Optional[dict] = None
    candidate_feedback: Optional[CandidateFeedbackResponse] = None
    primary_evidence: list[str]
    created_at: datetime


class BatchScreenResponse(BaseModel):
    """Response envelope for POST /api/v1/batch."""

    batch_id: str
    total: int
    results: list[ScreenResponse]


class RunListItem(BaseModel):
    """
    WHY: The list endpoint returns summary rows — not full run payloads.
    Callers fetch the full run via GET /runs/{run_id} when they need details.
    """

    run_id: UUID
    candidate_id: str
    role_type: str
    role_seniority: str
    verdict: str
    confidence_pct: float
    cost_usd: float
    created_at: datetime


class RunDetailResponse(BaseModel):
    """Full run payload returned by GET /runs/{run_id}."""

    run_id: UUID
    tenant_id: str
    candidate_id: str
    role_type: str
    role_seniority: str
    batch_id: Optional[str]
    verdict: str
    confidence_pct: float
    cost_usd: float
    ensemble_runs: int
    created_at: datetime


class OverrideResponse(BaseModel):
    """Response returned after a successful override is recorded."""

    run_id: UUID
    original_verdict: str
    override_verdict: str
    reason: str
    reviewer_id: str


class OutcomeResponse(BaseModel):
    """Response returned after a hire outcome is recorded."""

    run_id: UUID
    hired: bool
    performance_90d: Optional[str]
    notes: Optional[str]
