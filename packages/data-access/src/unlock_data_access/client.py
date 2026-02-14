"""Async database engine for Data Access activities.

Provides a lazy-initialized SQLAlchemy async engine backed by asyncpg, connected
to Supabase's PostgreSQL via the direct connection pooler (port 5432, session mode).

Session mode is required because asyncpg uses prepared statements, which are
incompatible with transaction-mode pooling.

Usage in activities:
    from unlock_data_access.client import get_engine

    async with get_engine().begin() as conn:
        result = await conn.execute(select(people))
"""

from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Return a lazily-initialized async engine singleton.

    Reads SUPABASE_DB_URL from the environment. The URL should point to the
    Supabase direct connection pooler (session mode, port 5432) and use the
    postgresql:// scheme — we replace it with postgresql+asyncpg:// for the
    async driver.
    """
    global _engine
    if _engine is not None:
        return _engine

    db_url = os.environ.get("SUPABASE_DB_URL", "")
    if not db_url:
        raise RuntimeError(
            "SUPABASE_DB_URL environment variable is not set. "
            "Set it to the Supabase direct connection string (session pooler, port 5432)."
        )

    # Ensure we use the asyncpg driver
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

    _engine = create_async_engine(
        db_url,
        pool_size=10,
        max_overflow=0,
        pool_pre_ping=True,
    )
    return _engine


def reset_engine() -> None:
    """Reset the engine singleton — used in tests to inject mocks."""
    global _engine
    _engine = None
