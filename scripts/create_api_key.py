"""Bootstrap script: create and print a default API key for SCREEN.

Connects to the database using the async session factory and calls
get_or_create_default_key() from the api_keys repository. If a default
key already exists it is returned unchanged — running this script twice
is safe (idempotent).

Usage:
    poetry run python scripts/create_api_key.py
"""

import asyncio

from db.session import AsyncSessionLocal
from db.repositories.api_keys import get_or_create_default_key


async def main() -> None:
    """Open a DB session and print the raw default API key."""
    async with AsyncSessionLocal() as session:
        raw_key = await get_or_create_default_key(session)
        await session.commit()

    print(f"API key: {raw_key}")


if __name__ == "__main__":
    asyncio.run(main())
