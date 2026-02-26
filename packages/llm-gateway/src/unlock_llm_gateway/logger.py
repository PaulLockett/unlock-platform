"""LM call logging — captures every LLM call for offline evals and debugging.

Two components:

1. LmCallCollector(BaseCallback) — in-memory capture via on_lm_end().
   No I/O in the callback to avoid blocking the LLM call path.

2. flush_lm_calls() — sync write of collected calls to unlock.lm_calls.
   Called after each DSPy program returns. Best-effort: if flush fails,
   the activity still succeeds (logging should never break business logic).

Pattern: activity creates collector -> configures DSPy with it ->
runs program -> flushes calls to Supabase -> returns Result.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from dspy.utils.callback import BaseCallback

from unlock_llm_gateway.db import get_sync_engine
from unlock_llm_gateway.tables import lm_calls


@dataclass
class LmCallRecord:
    """Single captured LM call — stored in memory until flush."""

    model: str = ""
    prompt_messages: str = ""
    completion: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    error: str = ""


class LmCallCollector(BaseCallback):
    """DSPy callback that captures LM calls in-memory.

    Collects prompt/completion/tokens/latency for each LM call without
    performing any I/O. Calls are flushed to the database after the program
    completes via flush_lm_calls().
    """

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[LmCallRecord] = []
        self._call_starts: dict[str, float] = {}

    def on_lm_start(
        self,
        call_id: str,
        instance: Any = None,
        inputs: dict[str, Any] | None = None,
    ) -> None:
        self._call_starts[call_id] = time.monotonic()

    def on_lm_end(
        self,
        call_id: str,
        outputs: dict[str, Any] | None = None,
        exception: Exception | None = None,
    ) -> None:
        start = self._call_starts.pop(call_id, None)
        latency_ms = (time.monotonic() - start) * 1000 if start else 0.0
        outputs = outputs or {}

        record = LmCallRecord(
            model=str(outputs.get("model", "")),
            prompt_messages=json.dumps(outputs.get("messages", []), default=str),
            completion=str(outputs.get("outputs", "")),
            input_tokens=int(outputs.get("input_tokens", 0)),
            output_tokens=int(outputs.get("output_tokens", 0)),
            latency_ms=latency_ms,
            error=str(exception) if exception else "",
        )
        self.calls.append(record)


@dataclass
class FlushStats:
    """Result of a flush operation."""

    flushed: int = 0
    errors: int = 0
    error_messages: list[str] = field(default_factory=list)


def flush_lm_calls(
    collector: LmCallCollector,
    activity_name: str,
    caller_workflow_id: str = "",
) -> FlushStats:
    """Write collected LM calls to unlock.lm_calls. Best-effort.

    Uses a single batch INSERT for efficiency. If the batch fails,
    all records are reported as errors.

    Args:
        collector: The LmCallCollector that captured calls.
        activity_name: Name of the activity that ran (e.g. "translate_query").
        caller_workflow_id: Optional Temporal workflow ID for traceability.

    Returns:
        FlushStats with count of flushed records and any errors.
    """
    if not collector.calls:
        return FlushStats()

    stats = FlushStats()

    records = [
        {
            "activity_name": activity_name,
            "model": record.model,
            "prompt_messages": record.prompt_messages,
            "completion": record.completion,
            "input_tokens": record.input_tokens,
            "output_tokens": record.output_tokens,
            "latency_ms": record.latency_ms,
            "error": record.error or None,
            "caller_workflow_id": caller_workflow_id or None,
        }
        for record in collector.calls
    ]

    try:
        engine = get_sync_engine()
        with engine.begin() as conn:
            conn.execute(lm_calls.insert(), records)
            stats.flushed = len(records)
    except Exception as e:
        stats.errors = len(records)
        stats.error_messages.append(f"Flush error: {e}")

    return stats
