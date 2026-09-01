"""Alembic environment configuration for async SQLAlchemy engine.

Uses asyncpg via run_sync to bridge the async engine into Alembic's
synchronous migration context. Both offline (SQL script generation) and
online (live database) modes are supported.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import Base so autogenerate can detect model changes
from db.models import Base  # noqa: E402

# Alembic Config object — provides access to values in alembic.ini
config = context.config

# Set up Python logging from the ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate comparisons
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit migration SQL to stdout without connecting to the database.

    Useful for generating migration scripts to review or apply manually.
    The sync URL from alembic.ini is used directly.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Execute migrations against an open synchronous connection.

    Called from the async wrapper below via run_sync so Alembic's synchronous
    context API is satisfied without blocking the event loop.

    Args:
        connection: Open SQLAlchemy synchronous Connection object.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and bridge into the synchronous migration context.

    NullPool is used so Alembic does not hold a connection pool open between
    migration steps — each migration command gets a fresh connection.
    """
    # Build an async engine from alembic.ini config, replacing the URL scheme
    # with the asyncpg variant so asyncpg is used as the driver.
    ini_section = config.get_section(config.config_ini_section, {})
    # Replace sync URL scheme with asyncpg scheme for the async engine
    sync_url: str = ini_section.get("sqlalchemy.url", "")
    async_url = sync_url.replace(
        "postgresql://", "postgresql+asyncpg://", 1
    ).replace(
        "postgresql+psycopg2://", "postgresql+asyncpg://", 1
    )
    ini_section["sqlalchemy.url"] = async_url

    connectable = async_engine_from_config(
        ini_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode.

    Runs the async migration coroutine inside a fresh event loop so Alembic's
    synchronous CLI stays compatible with the async engine.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
