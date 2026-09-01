"""Repository for ApiKey management.

The raw key is never stored — only its SHA-256 digest. This means a complete
database dump cannot be used to impersonate tenants. The raw key is returned
exactly once (at creation time) and the caller must store it securely.
"""

import hashlib
import secrets

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import ApiKey


def _hash_key(raw_key: str) -> str:
    """Return the SHA-256 hex digest of a raw API key.

    Args:
        raw_key: The plaintext API key string.

    Returns:
        64-character lowercase hex string.
    """
    return hashlib.sha256(raw_key.encode()).hexdigest()


async def create_api_key(
    session: AsyncSession,
    tenant_id: str,
    label: str | None = None,
) -> tuple[str, ApiKey]:
    """Generate a new API key, persist its hash, and return the raw key.

    The raw key follows the format ``sk_<64 random hex chars>``. It is returned
    to the caller exactly once — the database only ever sees the SHA-256 hash.

    Args:
        session: Active async database session.
        tenant_id: Tenant this key belongs to.
        label: Optional human-readable label (e.g. "production", "ci").

    Returns:
        A (raw_key, ApiKey) tuple. Store raw_key immediately — it cannot be
        recovered from the database after this function returns.
    """
    raw_key = "sk_" + secrets.token_hex(32)
    key_hash = _hash_key(raw_key)
    api_key = ApiKey(
        key_hash=key_hash,
        tenant_id=tenant_id,
        label=label,
    )
    session.add(api_key)
    await session.flush()
    return raw_key, api_key


async def verify_api_key(session: AsyncSession, raw_key: str) -> ApiKey | None:
    """Look up an API key by its hash, check it is active, and increment the counter.

    Args:
        session: Active async database session.
        raw_key: The plaintext API key submitted by the caller.

    Returns:
        The matching ApiKey if found and active, otherwise None.
    """
    key_hash = _hash_key(raw_key)
    result = await session.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
    )
    api_key = result.scalar_one_or_none()
    if api_key is not None:
        # Increment in-place; caller's session commit will persist this.
        api_key.requests_count += 1
        session.add(api_key)
    return api_key


async def get_or_create_default_key(session: AsyncSession) -> str:
    """Return a dev bootstrap key, creating one if none exist.

    Intended for local development only. If the api_keys table is empty, a key
    is created with tenant_id="default" and the raw key is printed to stdout so
    the developer can copy it into their .env file.

    Args:
        session: Active async database session (will be flushed but not
            committed — caller controls the transaction).

    Returns:
        The raw API key string (newly created or a placeholder message if keys
        already exist). In the existing-keys case the raw value cannot be
        recovered — rotate via create_api_key() instead.
    """
    count_result = await session.execute(
        select(func.count()).select_from(ApiKey)
    )
    count = count_result.scalar_one()

    if count > 0:
        # Keys already exist; we cannot reveal a stored raw key.
        return "[existing keys present — use create_api_key() to issue a new one]"

    raw_key, _ = await create_api_key(
        session, tenant_id="default", label="dev-bootstrap"
    )
    print(  # noqa: T201  — intentional stdout output for dev bootstrap
        f"\n[SCREEN] Dev bootstrap API key created:\n  {raw_key}\n"
        "  Add this to your .env as SCREEN_API_KEY and do not share it.\n"
    )
    return raw_key
