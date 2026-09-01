"""
WHY: The screen routes are the primary value surface of the API. A single
candidate or a batch of candidates comes in; a structured, persisted verdict
comes out. All business logic stays in the agent layer — these handlers are
pure orchestration: call runner, persist results, return response.

HOW: screen_candidate() / screen_batch() from the runner are awaited. Results
are persisted to DB (run, evidence claims, trajectory) before the response is
returned so callers always get a run_id they can query later.

Error handling: if the agent returns an error_message, we return HTTP 500
rather than a partial success — callers should not trust a run that errored.
"""

import hashlib
import time
from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import authenticate_request
from api.schemas import (
    BatchScreenRequest,
    BatchScreenResponse,
    CandidateFeedbackResponse,
    ScreenRequest,
    ScreenResponse,
)
from db.repositories.runs import RunRepository
from db.session import get_session
from screen.agent.runner import screen_batch, screen_candidate
from screen.schemas.input import ScreeningInput
from screen.schemas.state import ScreeningState

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["screening"])


# ── Internal helpers ──────────────────────────────────────────────────────────


def _build_screening_input(req: ScreenRequest) -> ScreeningInput:
    """
    WHY: Explicit mapping from API request to internal ScreeningInput.
    Keeping this as a named function makes it testable in isolation and
    means the mapping decision is documented in one place.

    Args:
        req: Validated API request body.

    Returns:
        ScreeningInput ready for the runner.
    """
    return ScreeningInput(
        candidate_id=req.candidate_id,
        role_seniority=req.role_seniority,
        role_type=req.role_type,
        cv_text=req.cv_text,
        job_description=req.job_description,
        hard_requirements=req.hard_requirements,
        batch_id=req.batch_id,
    )


def _build_run_data(
    state: ScreeningState,
    tenant_id: str,
    req: ScreenRequest,
    start_ms: float,
) -> dict:
    """
    WHY: Centralises the mapping from ScreeningState → DB run_data dict so
    both /screen and /batch handlers stay free of repetitive field extraction.

    Args:
        state: Completed ScreeningState from the runner.
        tenant_id: Extracted from the authenticated ApiKey.
        req: Original ScreenRequest for fields not in state.
        start_ms: Wall-clock start time (ms) for duration calculation.

    Returns:
        dict ready for RunRepository.create_run().
    """
    decision = state.get("decision")
    verdict = decision.verdict if decision else "ERROR"
    confidence_pct = decision.confidence_pct if decision else 0.0
    cost_usd = decision.estimated_cost_usd if decision else state.get("total_cost_usd", 0.0)

    cv_text_hash = hashlib.sha256(req.cv_text.encode()).hexdigest()

    return {
        "tenant_id": tenant_id,
        "candidate_id": req.candidate_id,
        "role_type": req.role_type,
        "role_seniority": req.role_seniority,
        "batch_id": req.batch_id,
        "verdict": verdict,
        "confidence_pct": confidence_pct,
        "cost_usd": cost_usd,
        "ensemble_runs": 1,
        "cv_text_hash": cv_text_hash,
        "duration_ms": int((time.time() * 1000) - start_ms),
    }


def _build_screen_response(
    state: ScreeningState,
    run_id: object,
    candidate_id: str,
    start_ms: float,
    created_at: datetime,
) -> ScreenResponse:
    """
    WHY: Extracts the public-facing fields from the ScreeningState and maps them
    to the ScreenResponse. Isolated here so batch and single handlers share logic.

    Args:
        state: Completed ScreeningState.
        run_id: UUID assigned by RunRepository.create_run().
        candidate_id: Candidate identifier.
        start_ms: Wall-clock start in ms for duration.
        created_at: Timestamp of the run creation.

    Returns:
        ScreenResponse ready to return to the caller.
    """
    decision = state.get("decision")
    human_brief = state.get("human_brief")
    feedback = state.get("candidate_feedback")

    verdict = decision.verdict if decision else "ERROR"
    confidence_pct = decision.confidence_pct if decision else 0.0
    cost_usd = decision.estimated_cost_usd if decision else state.get("total_cost_usd", 0.0)
    primary_evidence = decision.primary_evidence if decision else []
    escalated = verdict == "ESCALATE"

    feedback_response: Optional[CandidateFeedbackResponse] = None
    if feedback:
        feedback_response = CandidateFeedbackResponse(
            genuine_strength=feedback.genuine_strength,
            gap_for_this_role=feedback.gap_for_this_role,
            encouragement=feedback.encouragement,
        )

    human_brief_dict: Optional[dict] = None
    if human_brief:
        # WHY: model_dump() serialises the frozen Pydantic model to a plain dict
        # so the JSON response doesn't embed a nested Pydantic object.
        human_brief_dict = human_brief.model_dump()

    return ScreenResponse(
        run_id=run_id,  # type: ignore[arg-type]
        candidate_id=candidate_id,
        verdict=verdict,
        confidence_pct=confidence_pct,
        cost_usd=cost_usd,
        duration_ms=int((time.time() * 1000) - start_ms),
        ensemble_runs=1,
        escalated=escalated,
        human_brief=human_brief_dict,
        candidate_feedback=feedback_response,
        primary_evidence=list(primary_evidence),
        created_at=created_at,
    )


async def _persist_run(
    session: AsyncSession,
    state: ScreeningState,
    run_data: dict,
) -> object:
    """
    WHY: Persist the run, evidence claims, and trajectory in one call so both
    /screen and /batch handlers don't duplicate the three-step DB write sequence.

    Args:
        session: Active async SQLAlchemy session.
        state: Completed ScreeningState — source for evidence + trajectory.
        run_data: Pre-built dict for RunRepository.create_run().

    Returns:
        The created ScreeningRun ORM object (has .id as UUID).
    """
    db_run = await RunRepository.create_run(session, run_data)

    # Persist evidence claims — Claim.text maps to DB column claim_text
    evidence_bundle = state.get("evidence_bundle")
    if evidence_bundle:
        claims_dicts: list[dict] = [
            {"claim_text": claim.text, "tier": str(claim.tier)}
            for claim in (evidence_bundle.claims or [])
        ]
        for c in (evidence_bundle.contradictions or []):
            claims_dicts.append({
                "claim_text": f"{c.claim_a} ↔ {c.claim_b}",
                "tier": "D",
                "is_contradiction": True,
            })
        for f in (evidence_bundle.silence_flags or []):
            claims_dicts.append({
                "claim_text": f.absence_interpretation,
                "tier": "C",
                "is_silence_flag": True,
                "severity": str(getattr(f, "severity", "medium")),
            })
        if claims_dicts:
            await RunRepository.add_evidence_claims(session, db_run.id, claims_dicts)

    # Persist trajectory — TrajectoryEntry is a frozen Pydantic model; access
    # fields as attributes (.node, .duration_ms, etc.) not dict keys.
    trajectory = state.get("trajectory", [])
    if trajectory:
        trajectory_dicts = [
            {
                "node_name": entry.node,
                "reasoning_summary": entry.reasoning_summary,
                "duration_ms": entry.duration_ms,
                "cost_usd": entry.cost_usd,
                "sequence_order": i,
            }
            for i, entry in enumerate(trajectory)
        ]
        await RunRepository.add_trajectory(session, db_run.id, trajectory_dicts)

    return db_run


# ── Route handlers ────────────────────────────────────────────────────────────


@router.post("/screen", response_model=ScreenResponse, status_code=status.HTTP_200_OK)
async def screen_single(
    req: ScreenRequest,
    api_key: object = Depends(authenticate_request),
    session: AsyncSession = Depends(get_session),
) -> ScreenResponse:
    """
    WHY: Single-candidate screening endpoint. The primary call pattern for
    integrations that submit candidates one at a time (e.g. ATS webhook on
    new application).

    HOW:
      1. Call screen_candidate() with the validated input.
      2. Check for pipeline error — surface as HTTP 500 if set.
      3. Persist run, evidence claims, and trajectory to DB.
      4. Return structured response with run_id for future lookup.

    Args:
        req: Validated ScreenRequest body.
        api_key: Authenticated ApiKey ORM object from Depends(authenticate_request).
        session: SQLAlchemy session from Depends(get_session).

    Returns:
        ScreenResponse with verdict, confidence, cost, and run_id.

    Raises:
        HTTPException 500: If the screening pipeline returns an error_message.
    """
    tenant_id: str = api_key.tenant_id  # type: ignore[attr-defined]
    start_ms = time.time() * 1000

    logger.info(
        "screen_single: request received",
        candidate_id=req.candidate_id,
        role_seniority=req.role_seniority,
        role_type=req.role_type,
        tenant_id=tenant_id,
    )

    screening_input = _build_screening_input(req)
    state = await screen_candidate(screening_input)

    # WHY: Any pipeline error is surfaced as HTTP 500 so callers don't
    # silently process a partial/error run as a valid verdict.
    error_message = state.get("error_message")
    if error_message:
        logger.error(
            "screen_single: pipeline error",
            candidate_id=req.candidate_id,
            error=error_message,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Screening pipeline error: {error_message}",
        )

    run_data = _build_run_data(state, tenant_id, req, start_ms)
    db_run = await _persist_run(session, state, run_data)
    created_at = datetime.now(tz=timezone.utc)

    response = _build_screen_response(state, db_run.id, req.candidate_id, start_ms, created_at)

    logger.info(
        "screen_single: response built",
        candidate_id=req.candidate_id,
        verdict=response.verdict,
        confidence_pct=response.confidence_pct,
        run_id=str(response.run_id),
        tenant_id=tenant_id,
    )

    return response


@router.post("/batch", response_model=BatchScreenResponse, status_code=status.HTTP_200_OK)
async def screen_batch_endpoint(
    req: BatchScreenRequest,
    api_key: object = Depends(authenticate_request),
    session: AsyncSession = Depends(get_session),
) -> BatchScreenResponse:
    """
    WHY: Batch screening enables concurrent evaluation of a candidate pool for
    the same role. Callers submit all candidates at once; the runner fans them
    out concurrently so total wall-clock time is O(max_pipeline_time), not
    O(n * avg_pipeline_time).

    HOW:
      1. Assign a shared batch_id if not provided in any candidate.
      2. Call screen_batch() for concurrent processing.
      3. Persist each run individually (same DB write pattern as /screen).
      4. Return all results in input order.

    Args:
        req: BatchScreenRequest with a list of ScreenRequest objects.
        api_key: Authenticated ApiKey ORM object.
        session: SQLAlchemy session.

    Returns:
        BatchScreenResponse with batch_id, total count, and list of ScreenResponse.

    Raises:
        HTTPException 500: If any candidate's pipeline returns an error_message.
    """
    tenant_id: str = api_key.tenant_id  # type: ignore[attr-defined]
    batch_start_ms = time.time() * 1000

    # Derive a stable batch_id — prefer the first candidate's batch_id if set
    batch_id = req.candidates[0].batch_id or f"batch-{int(batch_start_ms)}"

    # Inject batch_id into any candidates that don't have one
    candidates_with_batch: list[ScreenRequest] = [
        ScreenRequest(
            candidate_id=c.candidate_id,
            role_seniority=c.role_seniority,
            role_type=c.role_type,
            cv_text=c.cv_text,
            job_description=c.job_description,
            hard_requirements=c.hard_requirements,
            batch_id=batch_id,
        )
        for c in req.candidates
    ]

    logger.info(
        "screen_batch_endpoint: request received",
        batch_id=batch_id,
        total=len(candidates_with_batch),
        tenant_id=tenant_id,
    )

    inputs = [_build_screening_input(c) for c in candidates_with_batch]
    states = await screen_batch(inputs)

    results: list[ScreenResponse] = []
    created_at = datetime.now(tz=timezone.utc)

    for candidate_req, state in zip(candidates_with_batch, states):
        error_message = state.get("error_message")
        if error_message:
            logger.error(
                "screen_batch_endpoint: pipeline error for candidate",
                candidate_id=candidate_req.candidate_id,
                error=error_message,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Pipeline error for {candidate_req.candidate_id}: {error_message}",
            )

        run_data = _build_run_data(state, tenant_id, candidate_req, batch_start_ms)
        run_data["batch_id"] = batch_id  # ensure batch_id is consistent
        db_run = await _persist_run(session, state, run_data)

        response = _build_screen_response(
            state, db_run.id, candidate_req.candidate_id, batch_start_ms, created_at
        )
        results.append(response)

    logger.info(
        "screen_batch_endpoint: complete",
        batch_id=batch_id,
        total=len(results),
        verdicts=[r.verdict for r in results],
        tenant_id=tenant_id,
    )

    return BatchScreenResponse(
        batch_id=batch_id,
        total=len(results),
        results=results,
    )
