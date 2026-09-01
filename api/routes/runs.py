"""
WHY: The runs routes provide read access to persisted screening runs.
Two endpoints: one for a specific run (full detail), one for the tenant's
run list (summary rows, paginated). All queries are scoped to the
authenticated tenant — no cross-tenant data access.

HOW: RunRepository handles all DB access. Route handlers do mapping only.
"""

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import authenticate_request
from api.schemas import RunDetailResponse, RunListItem
from db.repositories.runs import RunRepository
from db.session import get_session

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["runs"])


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
async def get_run(
    run_id: UUID,
    api_key: object = Depends(authenticate_request),
    session: AsyncSession = Depends(get_session),
) -> RunDetailResponse:
    """
    WHY: Callers need to retrieve the full details of a completed run —
    e.g. to render a recruiter dashboard card or build an audit export.

    HOW: RunRepository.get_run() fetches by UUID. Returns 404 if not found
    so callers get a clear signal rather than an empty response body.

    Args:
        run_id: UUID of the screening run, from the path parameter.
        api_key: Authenticated ApiKey (for tenant context).
        session: SQLAlchemy session.

    Returns:
        RunDetailResponse with full run fields.

    Raises:
        HTTPException 404: If the run_id does not exist in the DB.
    """
    tenant_id: str = api_key.tenant_id  # type: ignore[attr-defined]

    logger.info("get_run: fetching", run_id=str(run_id), tenant_id=tenant_id)

    db_run = await RunRepository.get_run(session, run_id)

    if db_run is None:
        logger.warning("get_run: not found", run_id=str(run_id), tenant_id=tenant_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found",
        )

    return RunDetailResponse(
        run_id=db_run.id,
        tenant_id=db_run.tenant_id,
        candidate_id=db_run.candidate_id,
        role_type=db_run.role_type,
        role_seniority=db_run.role_seniority,
        batch_id=db_run.batch_id,
        verdict=db_run.verdict,
        confidence_pct=db_run.confidence_pct,
        cost_usd=db_run.cost_usd,
        ensemble_runs=db_run.ensemble_runs,
        created_at=db_run.created_at,
    )


@router.get("/runs", response_model=list[RunListItem])
async def list_runs(
    limit: int = Query(default=20, ge=1, le=100, description="Page size"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    api_key: object = Depends(authenticate_request),
    session: AsyncSession = Depends(get_session),
) -> list[RunListItem]:
    """
    WHY: The run list lets callers build dashboards showing all candidates
    screened under their tenant. Pagination is enforced to prevent accidental
    full-table fetches on large tenants.

    HOW: RunRepository.list_runs() takes tenant_id, limit, offset — all runs
    returned are already scoped to the tenant. No cross-tenant filtering needed
    in the handler.

    Args:
        limit: Max rows to return. Capped at 100. Default 20.
        offset: Skip this many rows. Default 0.
        api_key: Authenticated ApiKey (provides tenant_id).
        session: SQLAlchemy session.

    Returns:
        List of RunListItem summary rows in descending created_at order.
    """
    tenant_id: str = api_key.tenant_id  # type: ignore[attr-defined]

    logger.info(
        "list_runs: fetching",
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )

    db_runs = await RunRepository.list_runs(session, tenant_id, limit=limit, offset=offset)

    return [
        RunListItem(
            run_id=run.id,
            candidate_id=run.candidate_id,
            role_type=run.role_type,
            role_seniority=run.role_seniority,
            verdict=run.verdict,
            confidence_pct=run.confidence_pct,
            cost_usd=run.cost_usd,
            created_at=run.created_at,
        )
        for run in db_runs
    ]
