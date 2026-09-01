"""
WHY: API key authentication is the single security boundary for all non-health
endpoints. Every request must carry a valid X-API-Key header. The key is
verified against the database on each request — no in-memory caching in v0.1
to keep the implementation simple and auditable.

HOW: FastAPI's Security() mechanism is used rather than a plain Depends() so
that the OpenAPI docs render a proper security scheme and the swagger UI
prompts for the key. authenticate_request is injected into route handlers
via Depends(authenticate_request).

The ApiKey object returned by verify_api_key carries tenant_id, which route
handlers use to scope all DB queries to the correct tenant.
"""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from db.repositories.api_keys import verify_api_key
from db.session import get_session

# WHY: APIKeyHeader reads from the X-API-Key request header. auto_error=False
# lets us return a consistent 401 (not a FastAPI-generated 403) when the
# header is missing.
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def authenticate_request(
    raw_key: str = Security(_api_key_header),
    session: AsyncSession = Depends(get_session),
) -> object:
    """
    WHY: Central authentication dependency. All protected routes declare
    Depends(authenticate_request) — auth logic lives in exactly one place.

    HOW: verify_api_key hashes the raw key and looks it up in the DB. Returns
    the ApiKey ORM object if found and active; None otherwise.

    Args:
        raw_key: The raw API key from the X-API-Key header. None if header absent.
        session: SQLAlchemy session injected by Depends(get_session).

    Returns:
        The validated ApiKey ORM object. Callers access .tenant_id from it.

    Raises:
        HTTPException 401: If the key is missing, not found, or inactive.
    """
    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    api_key = await verify_api_key(session, raw_key)

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key
