"""SQLAlchemy 2.0 ORM models for the SCREEN database schema.

All tables use UUID primary keys (Python-side default via uuid.uuid4) and
timezone-aware timestamps with server_default=func.now(). Relationships are
declared on ScreeningRun as the central aggregate root.
"""

import uuid
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Shared declarative base for all SCREEN models."""

    pass


class ApiKey(Base):
    """Stores hashed API keys for tenant authentication.

    The raw key is never persisted — only its SHA-256 digest is stored so a
    database breach cannot expose live credentials.
    """

    __tablename__ = "api_keys"
    __table_args__ = (Index("ix_api_keys_key_hash", "key_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    key_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    label: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requests_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<ApiKey id={self.id!s} tenant_id={self.tenant_id!r} "
            f"label={self.label!r} is_active={self.is_active}>"
        )


class ScreeningRun(Base):
    """Records one complete screening pipeline execution for a candidate.

    ensemble_runs indicates whether the verdict is the result of a single
    pipeline pass (1) or a 3-run ensemble with majority-vote aggregation (3).
    cv_text_hash enables cheap duplicate-detection before running the pipeline.
    """

    __tablename__ = "screening_runs"
    __table_args__ = (
        Index("ix_screening_runs_tenant_id", "tenant_id"),
        Index("ix_screening_runs_batch_id", "batch_id"),
        Index("ix_screening_runs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False)
    candidate_id: Mapped[str] = mapped_column(String(256), nullable=False)
    role_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    role_seniority: Mapped[str | None] = mapped_column(String(64), nullable=True)
    batch_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ensemble_runs: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cv_text_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships — children cascade-delete when the run is removed
    evidence_claims: Mapped[list["EvidenceClaim"]] = relationship(
        "EvidenceClaim", back_populates="run", cascade="all, delete-orphan"
    )
    trajectory_entries: Mapped[list["TrajectoryEntry"]] = relationship(
        "TrajectoryEntry",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="TrajectoryEntry.sequence_order",
    )
    human_override: Mapped["HumanOverride | None"] = relationship(
        "HumanOverride", back_populates="run", cascade="all, delete-orphan", uselist=False
    )
    hire_outcome: Mapped["HireOutcome | None"] = relationship(
        "HireOutcome", back_populates="run", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return (
            f"<ScreeningRun id={self.id!s} candidate_id={self.candidate_id!r} "
            f"verdict={self.verdict!r} tenant_id={self.tenant_id!r}>"
        )


class EvidenceClaim(Base):
    """A single evidence claim extracted by the pipeline for a screening run.

    Tier (A/B/C/D) signals source reliability. Contradiction and silence flags
    are set by the cross-validation node; severity drives the human-review
    threshold in the routing logic.
    """

    __tablename__ = "evidence_claims"
    __table_args__ = (Index("ix_evidence_claims_run_id", "run_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("screening_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    tier: Mapped[str] = mapped_column(String(4), nullable=False)
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_contradiction: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_silence_flag: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    severity: Mapped[str | None] = mapped_column(String(32), nullable=True)

    run: Mapped["ScreeningRun"] = relationship(
        "ScreeningRun", back_populates="evidence_claims"
    )

    def __repr__(self) -> str:
        return (
            f"<EvidenceClaim id={self.id!s} run_id={self.run_id!s} "
            f"tier={self.tier!r} is_contradiction={self.is_contradiction}>"
        )


class TrajectoryEntry(Base):
    """Records a single LangGraph node execution within a screening run.

    sequence_order allows the full reasoning trajectory to be reconstructed
    in execution order regardless of insertion timing. cost_usd here is the
    per-node LLM cost; summing over a run_id gives the total pipeline cost.
    """

    __tablename__ = "trajectory_entries"
    __table_args__ = (Index("ix_trajectory_entries_run_id", "run_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("screening_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_name: Mapped[str] = mapped_column(String(64), nullable=False)
    reasoning_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)

    run: Mapped["ScreeningRun"] = relationship(
        "ScreeningRun", back_populates="trajectory_entries"
    )

    def __repr__(self) -> str:
        return (
            f"<TrajectoryEntry id={self.id!s} run_id={self.run_id!s} "
            f"node_name={self.node_name!r} sequence_order={self.sequence_order}>"
        )


class HumanOverride(Base):
    """Records a reviewer's manual verdict override for a screening run.

    The UNIQUE constraint on run_id enforces the one-override-per-run business
    rule at the database level. reviewer_id is nullable to support anonymous
    review workflows.
    """

    __tablename__ = "human_overrides"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("screening_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    original_verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    override_verdict: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    run: Mapped["ScreeningRun"] = relationship(
        "ScreeningRun", back_populates="human_override"
    )

    def __repr__(self) -> str:
        return (
            f"<HumanOverride id={self.id!s} run_id={self.run_id!s} "
            f"original={self.original_verdict!r} override={self.override_verdict!r}>"
        )


class HireOutcome(Base):
    """Records the real-world hiring decision and optional 90-day performance rating.

    Persisting outcomes enables future calibration of the pipeline's verdict
    accuracy against ground truth. The UNIQUE constraint mirrors HumanOverride —
    one factual outcome per run.
    """

    __tablename__ = "hire_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("screening_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    hired: Mapped[bool] = mapped_column(Boolean, nullable=False)
    performance_90d: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    run: Mapped["ScreeningRun"] = relationship(
        "ScreeningRun", back_populates="hire_outcome"
    )

    def __repr__(self) -> str:
        return (
            f"<HireOutcome id={self.id!s} run_id={self.run_id!s} "
            f"hired={self.hired} performance_90d={self.performance_90d!r}>"
        )
