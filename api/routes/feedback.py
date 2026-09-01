"""
WHY: Feedback routes close the human-in-the-loop cycle. Human overrides and hire
outcomes are the ground-truth labels that make SCREEN improvable over time. Without
capturing them, every run starts from the same uncalibrated baseline.

HOW: Two endpoints — one for verdict overrides (immediate, by a reviewer), one for
90-day hire outcomes (delayed, by the hiring manager). Both validate the run exists
and belongs to the authenticated tenant before writing.
"""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import authenticate_request
from api.schemas import OutcomeRequest, OutcomeResponse, OverrideRequest, OverrideResponse
from db.repositories.feedback import record_outcome, record_override
from db.repositories.runs import RunRepository
from db.session import get_session

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["feedback"])


@router.post(
    "/runs/{run_id}/override",
    response_model=OverrideResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_override(
    run_id: uuid.UUID,
    req: OverrideRequest,
    api_key: object = Depends(authenticate_request),
    session: AsyncSession = Depends(get_session),
) -> OverrideResponse:
    """Record a reviewer's manual verdict override for a screening run.

    WHY: Every override is a training signal. When SCREEN says NO and a human says YES,
    that disagreement tells us what the pipeline missed. Capturing it with a required
    reason field makes it legible for future calibration.

    Args:
        run_id: UUID of the ScreeningRun being overridden.
        req: OverrideRequest with new verdict and required reason.
        api_key: Authenticated ApiKey — provides tenant and reviewer identity.
        session: Async DB session.

    Returns:
        OverrideResponse confirming the recorded override.

    Raises:
        HTTPException 404: Run not found or belongs to another tenant.
        HTTPException 409: Override already recorded for this run.
    """
    tenant_id: str = api_key.tenant_id  # type: ignore[attr-defined]
    reviewer_id: str = str(getattr(api_key, "id", tenant_id))

    db_run = await RunRepository.get_run(session, run_id)
    if db_run is None or db_run.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found")

    original_verdict: str = db_run.verdict

    try:
        await record_override(
            session=session,
            run_id=run_id,
            original_verdict=original_verdict,
            override_verdict=req.override_verdict,
            reason=req.reason,
            reviewer_id=reviewer_id,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Override already recorded for run {run_id}",
        )

    logger.info(
        "submit_override: recorded",
        run_id=str(run_id),
        original=original_verdict,
        override=req.override_verdict,
        tenant_id=tenant_id,
    )

    return OverrideResponse(
        run_id=run_id,
        original_verdict=original_verdict,
        override_verdict=req.override_verdict,
        reason=req.reason,
        reviewer_id=reviewer_id,
    )


@router.post(
    "/runs/{run_id}/outcome",
    response_model=OutcomeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_outcome(
    run_id: uuid.UUID,
    req: OutcomeRequest,
    api_key: object = Depends(authenticate_request),
    session: AsyncSession = Depends(get_session),
) -> OutcomeResponse:
    """Record the real-world hiring decision and optional 90-day performance rating.

    WHY: Outcome data is the ultimate ground truth for calibration. A STRONG_YES that
    turned out to be a poor performer is the most valuable signal for improving accuracy.

    Args:
        run_id: UUID of the ScreeningRun this outcome refers to.
        req: OutcomeRequest with hired flag and optional performance rating.
        api_key: Authenticated ApiKey.
        session: Async DB session.

    Returns:
        OutcomeResponse confirming the recorded outcome.

    Raises:
        HTTPException 404: Run not found or belongs to another tenant.
        HTTPException 409: Outcome already recorded for this run.
    """
    tenant_id: str = api_key.tenant_id  # type: ignore[attr-defined]

    db_run = await RunRepository.get_run(session, run_id)
    if db_run is None or db_run.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found")

    try:
        await record_outcome(
            session=session,
            run_id=run_id,
            hired=req.hired,
            performance_90d=req.performance_90d,
            notes=req.notes,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Outcome already recorded for run {run_id}",
        )

    logger.info(
        "submit_outcome: recorded",
        run_id=str(run_id),
        hired=req.hired,
        performance_90d=req.performance_90d,
        tenant_id=tenant_id,
    )

    return OutcomeResponse(
        run_id=run_id,
        hired=req.hired,
        performance_90d=req.performance_90d,
        notes=req.notes,
    )
