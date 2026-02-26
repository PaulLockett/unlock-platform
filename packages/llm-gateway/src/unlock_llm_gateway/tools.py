"""RLM database tools — sync Python functions exposed to the ReAct sandbox.

Three tools for database exploration and read-only query execution:
  1. execute_sql — Run a SELECT query and get JSON results
  2. list_tables — Enumerate tables in the unlock schema with row counts
  3. describe_table — Get column metadata for a specific table

Safety:
  - execute_sql rejects non-SELECT statements before execution
  - Uses SET TRANSACTION READ ONLY as a second guard
  - Returns max 500 rows to avoid memory blowout
"""

from __future__ import annotations

import json
import re

from sqlalchemy import text

from unlock_llm_gateway.db import get_sync_engine


def execute_sql(sql: str) -> str:
    """Execute a READ-ONLY SQL query and return results as JSON.

    Only SELECT statements are allowed. Returns up to 500 rows.

    Args:
        sql: A SQL SELECT statement to execute.

    Returns:
        JSON string with query results or error message.
    """
    # First guard: reject non-SELECT statements
    stripped = sql.strip().rstrip(";").strip()
    if not re.match(r"^\s*SELECT\b", stripped, re.IGNORECASE):
        return json.dumps({"error": "Only SELECT statements are allowed."})

    engine = get_sync_engine()
    try:
        with engine.connect() as conn:
            # Second guard: read-only transaction
            conn.execute(text("SET TRANSACTION READ ONLY"))
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows = [dict(zip(columns, row, strict=True)) for row in result.fetchmany(500)]
            return json.dumps(rows, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


def list_tables() -> str:
    """List all tables in the unlock schema with row counts.

    Returns:
        JSON string with table names and approximate row counts.
    """
    engine = get_sync_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT schemaname, tablename,
                           n_live_tup AS approximate_row_count
                    FROM pg_stat_user_tables
                    WHERE schemaname = 'unlock'
                    ORDER BY tablename
                    """
                )
            )
            columns = list(result.keys())
            rows = [dict(zip(columns, row, strict=True)) for row in result.fetchall()]
            return json.dumps(rows, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


def describe_table(table_name: str) -> str:
    """Return column names, types, and constraints for a table.

    Args:
        table_name: Table name (in the unlock schema).

    Returns:
        JSON string with column metadata.
    """
    engine = get_sync_engine()
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT column_name, data_type, is_nullable,
                           column_default, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_schema = 'unlock'
                      AND table_name = :table_name
                    ORDER BY ordinal_position
                    """
                ),
                {"table_name": table_name},
            )
            columns = list(result.keys())
            rows = [dict(zip(columns, row, strict=True)) for row in result.fetchall()]
            return json.dumps(rows, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
