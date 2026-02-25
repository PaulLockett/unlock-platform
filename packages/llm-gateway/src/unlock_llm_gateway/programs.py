"""DSPy language programs — the actual LLM reasoning logic.

Three programs, each a thin wrapper around a DSPy module:

1. run_translate_query — ChainOfThought NL to SQL
2. run_draft_schema — ChainOfThought NL to schema definition
3. run_analyze_data — RLM iterative QnA with database tools

All programs accept an `lm` parameter and use `dspy.context(lm=lm)` for
per-call isolation. This avoids global state between concurrent activities.

These are sync functions — activities wrap them in asyncio.to_thread().
"""

from __future__ import annotations

from typing import Any

import dspy


def run_translate_query(question: str, schema_context: str, lm: dspy.LM) -> dict[str, str]:
    """Translate a natural language question to SQL.

    Uses ChainOfThought for step-by-step reasoning about the schema before
    producing the SQL query.

    Returns:
        Dict with "sql_query" and "explanation" keys.
    """
    program = dspy.ChainOfThought("question, schema_context -> sql_query, explanation")

    with dspy.context(lm=lm):
        result = program(question=question, schema_context=schema_context)

    return {
        "sql_query": result.sql_query,
        "explanation": result.explanation,
    }


def run_draft_schema(description: str, existing_context: str, lm: dspy.LM) -> dict[str, str]:
    """Generate a data model / schema definition from a natural language description.

    Uses ChainOfThought to reason about the description and existing context
    before producing a JSON schema definition.

    Returns:
        Dict with "schema_definition" and "explanation" keys.
    """
    program = dspy.ChainOfThought("description, existing_context -> schema_definition, explanation")

    with dspy.context(lm=lm):
        result = program(description=description, existing_context=existing_context)

    return {
        "schema_definition": result.schema_definition,
        "explanation": result.explanation,
    }


def run_analyze_data(
    question: str,
    tools: list[Any],
    lm: dspy.LM,
) -> dict[str, Any]:
    """Answer analytical questions via iterative SQL + reasoning + Python computation.

    Uses DSPy's ReAct module to explore the database schema, write SQL, execute
    queries, reason about results, and optionally run Python computations. The
    caller doesn't see any of this iteration — it's a function call in, structured
    answer out.

    Args:
        question: The analytical question to answer.
        tools: List of tool functions (execute_sql, list_tables, describe_table).
        lm: Configured DSPy LM instance.

    Returns:
        Dict with "answer", "sql_queries" (list), and "trajectory" keys.
    """
    program = dspy.ReAct(
        "question -> answer",
        tools=tools,
    )

    with dspy.context(lm=lm):
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
