"""SCREEN database package.

Public surface area intentionally kept minimal — callers import the engine and
session factory from db.session, and Base from db.models, for Alembic
compatibility and to avoid circular imports.
"""

from db.models import Base
from db.session import engine, get_session

__all__ = ["Base", "engine", "get_session"]
