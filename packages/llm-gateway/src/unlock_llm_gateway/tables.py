"""SQLAlchemy Core table definition for LM call logging.

Python-side mirror of the Supabase migration. Used by the logger to construct
typed, parameterized INSERT statements. NOT an ORM — just typed column references.
"""

from sqlalchemy import Column, DateTime, Float, Integer, MetaData, Table, Text
from sqlalchemy.dialects.postgresql import UUID

metadata = MetaData(schema="unlock")

lm_calls = Table(
    "lm_calls",
    metadata,
    Column("id", UUID, primary_key=True, server_default="gen_random_uuid()"),
    Column("activity_name", Text, nullable=False),
    Column("model", Text, nullable=False),
    Column("prompt_messages", Text, nullable=False),
    Column("completion", Text),
    Column("input_tokens", Integer),
    Column("output_tokens", Integer),
    Column("latency_ms", Float),
    Column("error", Text),
    Column("caller_workflow_id", Text),
    Column("created_at", DateTime(timezone=True), server_default="now()"),
)
