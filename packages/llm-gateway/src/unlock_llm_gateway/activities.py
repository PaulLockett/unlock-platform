"""LLM Gateway activities — 3 business verb operations + backward-compat shim.

Run on LLM_GATEWAY_QUEUE. Each activity wraps a DSPy language program with:
  - Request/Result boundary types from unlock_shared.llm_models
  - LM call logging via LmCallCollector + flush_lm_calls
  - asyncio.to_thread() to run sync DSPy calls without blocking the event loop

Business verbs follow the Righting Software test: "If I switched from DSPy
to direct API calls, would this operation name still make sense?"

Activities never raise — they return success=False on error so workflows
can handle failures without exception machinery.
"""

from __future__ import annotations

import asyncio

import dspy
from temporalio import activity
from unlock_shared.llm_models import (
    AnalyzeDataRequest,
    AnalyzeDataResult,
    DraftSchemaRequest,
    DraftSchemaResult,
    TranslateQueryRequest,
    TranslateQueryResult,
)

from unlock_llm_gateway.client import get_lm
from unlock_llm_gateway.logger import LmCallCollector, flush_lm_calls
from unlock_llm_gateway.programs import (
    run_analyze_data,
    run_draft_schema,
    run_translate_query,
)
from unlock_llm_gateway.tools import describe_table, execute_sql, list_tables


def _run_translate(
    question: str, schema_context: str, model: str, collector: LmCallCollector,
) -> dict:
    """Sync wrapper for translate_query DSPy program."""
    lm = get_lm(model)
    with dspy.context(lm=lm, callbacks=[collector]):
        return run_translate_query(question, schema_context, lm)


def _run_draft(
    description: str, existing_context: str, model: str, collector: LmCallCollector,
) -> dict:
    """Sync wrapper for draft_schema DSPy program."""
    lm = get_lm(model)
    with dspy.context(lm=lm, callbacks=[collector]):
        return run_draft_schema(description, existing_context, lm)


def _run_analyze(question: str, model: str, collector: LmCallCollector) -> dict:
    """Sync wrapper for analyze_data DSPy program with database tools."""
    lm = get_lm(model)
    tools = [execute_sql, list_tables, describe_table]
    with dspy.context(lm=lm, callbacks=[collector]):
        return run_analyze_data(question, tools, lm)


@activity.defn
async def translate_query(req: TranslateQueryRequest) -> TranslateQueryResult:
    """Convert a natural language question to SQL.

    Simple NL-to-SQL for search interfaces and straightforward queries.
    Uses ChainOfThought for step-by-step reasoning about the schema.
    """
    collector = LmCallCollector()

    try:
        result = await asyncio.to_thread(
            _run_translate, req.question, req.schema_context, req.model, collector
        )
        flush_lm_calls(collector, "translate_query")
        return TranslateQueryResult(
            success=True,
            message="Query translated successfully",
            sql_query=result["sql_query"],
            explanation=result["explanation"],
        )
    except Exception as e:
        flush_lm_calls(collector, "translate_query")
        return TranslateQueryResult(
            success=False,
            message=f"Failed to translate query: {e}",
        )


@activity.defn
async def draft_schema(req: DraftSchemaRequest) -> DraftSchemaResult:
    """Generate a data model / schema definition from a natural language description.

    Used by ConfigureWorkflow to let users describe what data they want to model
    and get a structured schema back.
    """
    collector = LmCallCollector()

    try:
        result = await asyncio.to_thread(
            _run_draft, req.description, req.existing_context, req.model, collector
        )
        flush_lm_calls(collector, "draft_schema")
        return DraftSchemaResult(
            success=True,
            message="Schema drafted successfully",
            schema_definition=result["schema_definition"],
            explanation=result["explanation"],
        )
    except Exception as e:
        flush_lm_calls(collector, "draft_schema")
        return DraftSchemaResult(
            success=False,
            message=f"Failed to draft schema: {e}",
        )


@activity.defn
async def analyze_data(req: AnalyzeDataRequest) -> AnalyzeDataResult:
    """Answer analytical questions via iterative SQL + reasoning + Python computation.

    The full QnA experience: the LLM explores the database schema, writes SQL,
    executes queries, reasons about results, and iterates until it has a complete
    answer. Single function call in, structured answer out.
    """
    collector = LmCallCollector()

    try:
        result = await asyncio.to_thread(
            _run_analyze, req.question, req.model, collector
        )
        flush_lm_calls(collector, "analyze_data")
        return AnalyzeDataResult(
            success=True,
            message="Analysis complete",
            answer=result["answer"],
            sql_queries_executed=result.get("sql_queries", []),
            trajectory=result.get("trajectory", ""),
        )
    except Exception as e:
        flush_lm_calls(collector, "analyze_data")
        return AnalyzeDataResult(
            success=False,
            message=f"Failed to analyze data: {e}",
        )


# ============================================================================
# Backward-compat shim — kept for existing Railway deployment
# ============================================================================


@activity.defn
async def hello_llm_assess(text: str) -> str:
    """Placeholder: simulates LLM-powered data quality assessment."""
    activity.logger.info(f"LLM Gateway: assessing '{text[:50]}'")
    return f"LLM assessment: {text}"
