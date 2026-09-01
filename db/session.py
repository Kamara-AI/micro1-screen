"""Async SQLAlchemy engine, session factory, and dependency helpers.

Uses asyncpg as the async driver. The engine is configured with pool_pre_ping
so stale connections are detected before use — critical for long-running
LangGraph pipelines that may idle between steps.

init_db() is intentionally kept for dev/test convenience; production table
creation is handled exclusively through Alembic migrations.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from db.models import Base

import os

_ASYNC_DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://screen_user:screen_pass@localhost:5433/screen_db",
)

engine = create_async_engine(
    _ASYNC_DB_URL,
    pool_pre_ping=True,
    pool_size=10,
    echo=False,  # Set to True locally for SQL query logging
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional AsyncSession and guarantee cleanup.

    Designed as a FastAPI/Starlette dependency but can be used in any async
    context manager. The session is committed on clean exit and rolled back if
    an exception propagates — the caller must not call commit() themselves when
    using this as a dependency.

    Yields:
        AsyncSession: An open, bound async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables defined on Base (dev/test only).

    This is NOT a substitute for Alembic migrations in production. Use this
    only in local development or pytest fixtures where you want a clean schema
    without running ``alembic upgrade head``.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
