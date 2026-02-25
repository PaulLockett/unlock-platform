"""LLM Gateway boundary models — the contract between callers and the LLM Gateway.

These types cross the Temporal activity boundary. Workflows in the Data Manager
(or any other component) create them as arguments; activities in the LLM Gateway
receive and return them.

Design choices:
  - Business verbs pass the Righting Software test: "If I switched from DSPy
    to direct API calls, would this name still make sense?" Yes — translate_query,
    draft_schema, analyze_data are all framework-agnostic.
  - Every request carries an optional model override so callers can A/B test
    models without gateway changes.
  - Results extend PlatformResult for consistent success/failure handling.
"""

from __future__ import annotations

from pydantic import BaseModel

from unlock_shared.models import PlatformResult

DEFAULT_MODEL = "openrouter/anthropic/claude-sonnet-4"

# ============================================================================
# translate_query — NL to SQL for search interfaces and simple queries
# ============================================================================


class TranslateQueryRequest(BaseModel):
    """Input for translate_query: convert a natural language question to SQL."""

    question: str
    schema_context: str
    model: str = ""


class TranslateQueryResult(PlatformResult):
    """Result of translate_query."""

    sql_query: str = ""
    explanation: str = ""


# ============================================================================
# draft_schema — NL to schema definition for ConfigureWorkflow
# ============================================================================


class DraftSchemaRequest(BaseModel):
    """Input for draft_schema: generate a data model from a description."""

    description: str
    existing_context: str = ""
    model: str = ""


class DraftSchemaResult(PlatformResult):
    """Result of draft_schema."""

    schema_definition: str = ""
    explanation: str = ""


# ============================================================================
# analyze_data — Full iterative QnA with SQL + reasoning + Python computation
# ============================================================================


class AnalyzeDataRequest(BaseModel):
    """Input for analyze_data: answer analytical questions via iterative exploration."""

    question: str
    model: str = ""


class AnalyzeDataResult(PlatformResult):
    """Result of analyze_data: structured answer with execution trajectory."""

    answer: str = ""
    sql_queries_executed: list[str] = []
    trajectory: str = ""
