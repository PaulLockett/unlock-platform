"""Sync database engine for LLM Gateway tool execution and LM call logging.

Own copy to avoid cross-layer dependency with data-access (which uses async).
The LLM Gateway needs sync connections because:
  1. RLM tools run in the host process as sync Python functions
  2. LM call logging flushes synchronously after each program completes

Reads SUPABASE_DB_URL from the environment. Uses psycopg2 (sync) driver.
"""

from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine

_engine: Engine | None = None


def get_sync_engine() -> Engine:
    """Return a lazily-initialized sync engine singleton.

    Reads SUPABASE_DB_URL from the environment and configures a sync
    SQLAlchemy engine with psycopg2.
    """
    global _engine
    if _engine is not None:
        return _engine

    db_url = os.environ.get("SUPABASE_DB_URL", "")
    if not db_url:
        raise RuntimeError(
            "SUPABASE_DB_URL environment variable is not set. "
            "Set it to the Supabase direct connection string."
        )

    # Ensure we use the psycopg2 sync driver
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)

    _engine = create_engine(
        db_url,
        pool_size=5,
        max_overflow=0,
        pool_pre_ping=True,
    )
    return _engine


def reset_engine() -> None:
    """Reset the engine singleton — used in tests to inject mocks."""
    global _engine
    _engine = None
