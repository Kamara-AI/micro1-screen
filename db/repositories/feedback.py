"""Repository for post-screening feedback: human overrides and hire outcomes.

Both tables enforce a UNIQUE constraint on run_id (one record per run). These
methods will raise IntegrityError if called twice for the same run — callers
should handle that at the API layer and surface it as a 409 Conflict.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import HireOutcome, HumanOverride


async def record_override(
    session: AsyncSession,
    run_id: uuid.UUID,
    original_verdict: str,
    override_verdict: str,
    reason: str,
    reviewer_id: str | None = None,
) -> HumanOverride:
    """Persist a reviewer's manual verdict override for a screening run.

    Raises sqlalchemy.exc.IntegrityError if an override already exists for
    this run_id (enforced by the UNIQUE constraint on human_overrides.run_id).

    Args:
        session: Active async database session.
        run_id: UUID of the ScreeningRun being overridden.
        original_verdict: The pipeline's verdict before the override.
        override_verdict: The reviewer's replacement verdict.
        reason: Free-text justification for the change.
        reviewer_id: Optional identifier of the reviewer (email, user ID, etc.).

    Returns:
        The persisted HumanOverride instance (flushed but not committed).
    """
    override = HumanOverride(
        run_id=run_id,
        original_verdict=original_verdict,
        override_verdict=override_verdict,
        reason=reason,
        reviewer_id=reviewer_id,
    )
    session.add(override)
    await session.flush()
    return override


async def record_outcome(
    session: AsyncSession,
    run_id: uuid.UUID,
    hired: bool,
    performance_90d: str | None = None,
    notes: str | None = None,
) -> HireOutcome:
    """Record the real-world hiring decision and optional 90-day performance rating.

    Raises sqlalchemy.exc.IntegrityError if an outcome already exists for this
    run_id. Use this to feed ground-truth labels back into the system for future
    calibration of pipeline accuracy.

    Args:
        session: Active async database session.
        run_id: UUID of the ScreeningRun this outcome refers to.
        hired: True if the candidate was hired, False if rejected.
        performance_90d: Optional 90-day rating: "excellent", "good",
            "average", or "poor".
        notes: Optional free-text notes from the hiring manager.

    Returns:
        The persisted HireOutcome instance (flushed but not committed).
    """
    outcome = HireOutcome(
        run_id=run_id,
        hired=hired,
        performance_90d=performance_90d,
        notes=notes,
    )
    session.add(outcome)
    await session.flush()
    return outcome
