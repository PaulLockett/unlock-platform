"""DSPy language programs — the actual LLM reasoning logic.

Three programs, each a thin wrapper around a DSPy module:

1. run_translate_query — ChainOfThought NL to SQL
2. run_draft_schema — ChainOfThought NL to schema definition
3. run_analyze_data — ReAct iterative QnA with database tools

Programs do NOT set their own dspy.context — they inherit the caller's
context (set by the sync wrappers in activities.py). This ensures that
callbacks (like LmCallCollector) survive through program execution.

These are sync functions — activities wrap them in asyncio.to_thread().
"""

from __future__ import annotations

from typing import Any

import dspy


def run_translate_query(question: str, schema_context: str) -> dict[str, str]:
    """Translate a natural language question to SQL.

    Uses ChainOfThought for step-by-step reasoning about the schema before
    producing the SQL query.

    Relies on the caller's dspy.context for LM and callbacks.

    Returns:
        Dict with "sql_query" and "explanation" keys.
    """
    program = dspy.ChainOfThought("question, schema_context -> sql_query, explanation")
    result = program(question=question, schema_context=schema_context)

    return {
        "sql_query": result.sql_query,
        "explanation": result.explanation,
    }


def run_draft_schema(description: str, existing_context: str) -> dict[str, str]:
    """Generate a data model / schema definition from a natural language description.

    Uses ChainOfThought to reason about the description and existing context
    before producing a JSON schema definition.

    Relies on the caller's dspy.context for LM and callbacks.

    Returns:
        Dict with "schema_definition" and "explanation" keys.
    """
    program = dspy.ChainOfThought("description, existing_context -> schema_definition, explanation")
    result = program(description=description, existing_context=existing_context)

    return {
        "schema_definition": result.schema_definition,
        "explanation": result.explanation,
    }


def run_analyze_data(
    question: str,
    tools: list[Any],
) -> dict[str, Any]:
    """Answer analytical questions via iterative SQL + reasoning + Python computation.

    Uses DSPy's ReAct module to explore the database schema, write SQL, execute
    queries, reason about results, and optionally run Python computations. The
    caller doesn't see any of this iteration — it's a function call in, structured
    answer out.

    Relies on the caller's dspy.context for LM and callbacks.

    Args:
        question: The analytical question to answer.
        tools: List of tool functions (execute_sql, list_tables, describe_table).

    Returns:
        Dict with "answer", "sql_queries" (list), and "trajectory" keys.
    """
    program = dspy.ReAct(
        "question -> answer",
        tools=tools,
    )
    result = program(question=question)

    # Extract trajectory from the ReAct execution for logging
    trajectory = ""
    if hasattr(result, "trajectory"):
        trajectory = str(result.trajectory)

    # Extract any SQL queries from trajectory observations
    sql_queries: list[str] = []
    if hasattr(result, "observations"):
        for obs in result.observations:
            obs_str = str(obs)
            if "SELECT" in obs_str.upper():
                sql_queries.append(obs_str)

    return {
        "answer": result.answer,
        "sql_queries": sql_queries,
        "trajectory": trajectory,
    }
