"""Repository for ScreeningRun and its child aggregates.

All methods accept an externally-provided AsyncSession so that callers control
transaction boundaries — this avoids hidden commits inside repository calls and
keeps the repository testable with a session mock.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import EvidenceClaim, ScreeningRun, TrajectoryEntry


class RunRepository:
    """Data-access methods for the screening_runs aggregate and its children."""

    @staticmethod
    async def create_run(session: AsyncSession, run_data: dict) -> ScreeningRun:
        """Persist a new ScreeningRun row.

        Args:
            session: Active async database session.
            run_data: Dict of column values. Unknown keys are ignored so callers
                can pass the full pipeline output dict without pre-filtering.

        Returns:
            The freshly-added ScreeningRun (not yet committed — caller controls
            the transaction).
        """
        allowed_columns = {
            "tenant_id",
            "candidate_id",
            "role_type",
            "role_seniority",
            "batch_id",
            "verdict",
            "confidence_pct",
            "cost_usd",
            "duration_ms",
            "ensemble_runs",
            "cv_text_hash",
        }
        filtered = {k: v for k, v in run_data.items() if k in allowed_columns}
        run = ScreeningRun(**filtered)
        session.add(run)
        await session.flush()  # Populate run.id without committing
        return run

    @staticmethod
    async def get_run(session: AsyncSession, run_id: uuid.UUID) -> ScreeningRun | None:
        """Fetch a single ScreeningRun with all child relations eagerly loaded.

        Eager-loading evidence_claims, trajectory_entries, human_override, and
        hire_outcome in one query prevents N+1 issues in the API layer.

        Args:
            session: Active async database session.
            run_id: UUID of the target run.

        Returns:
            The ScreeningRun if found, otherwise None.
        """
        result = await session.execute(
            select(ScreeningRun)
            .options(
                selectinload(ScreeningRun.evidence_claims),
                selectinload(ScreeningRun.trajectory_entries),
                selectinload(ScreeningRun.human_override),
                selectinload(ScreeningRun.hire_outcome),
            )
            .where(ScreeningRun.id == run_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_runs(
        session: AsyncSession,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ScreeningRun]:
        """Return a paginated list of ScreeningRuns for a tenant, newest first.

        Args:
            session: Active async database session.
            tenant_id: Scope results to this tenant.
            limit: Maximum number of rows to return (default 50).
            offset: Number of rows to skip for pagination (default 0).

        Returns:
            List of ScreeningRun objects, ordered by created_at descending.
        """
        result = await session.execute(
            select(ScreeningRun)
            .where(ScreeningRun.tenant_id == tenant_id)
            .order_by(ScreeningRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    @staticmethod
    async def add_evidence_claims(
        session: AsyncSession,
        run_id: uuid.UUID,
        claims: list[dict],
    ) -> None:
        """Bulk-insert EvidenceClaim rows for an existing run.

        Args:
            session: Active async database session.
            run_id: UUID of the parent ScreeningRun.
            claims: List of dicts with keys: tier, claim_text, and optionally
                is_contradiction, is_silence_flag, severity.
        """
        allowed_columns = {
            "tier",
            "claim_text",
            "is_contradiction",
            "is_silence_flag",
            "severity",
        }
        for claim_data in claims:
            filtered = {k: v for k, v in claim_data.items() if k in allowed_columns}
            claim = EvidenceClaim(run_id=run_id, **filtered)
            session.add(claim)
        await session.flush()

    @staticmethod
    async def add_trajectory(
        session: AsyncSession,
        run_id: uuid.UUID,
        entries: list[dict],
    ) -> None:
        """Bulk-insert TrajectoryEntry rows for an existing run.

        sequence_order must be provided in each entry dict — it is the caller's
        responsibility to assign correct ordering (typically the LangGraph node
        execution index).

        Args:
            session: Active async database session.
            run_id: UUID of the parent ScreeningRun.
            entries: List of dicts with keys: node_name, sequence_order, and
                optionally reasoning_summary, duration_ms, cost_usd.
        """
        allowed_columns = {
            "node_name",
            "reasoning_summary",
            "duration_ms",
            "cost_usd",
            "sequence_order",
        }
        for entry_data in entries:
            filtered = {k: v for k, v in entry_data.items() if k in allowed_columns}
            entry = TrajectoryEntry(run_id=run_id, **filtered)
            session.add(entry)
        await session.flush()
