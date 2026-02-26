"""Tests for LM call logging — collector callbacks and flush behavior.

The collector captures LM calls in-memory during DSPy program execution.
The flush writes them to the database afterward. Both must be robust:
the collector must handle edge cases without crashing, and the flush
must be best-effort (never break business logic).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from unlock_llm_gateway.logger import LmCallCollector, LmCallRecord, flush_lm_calls

# ============================================================================
# LmCallCollector
# ============================================================================


class TestLmCallCollector:
    def test_on_lm_start_records_timestamp(self):
        collector = LmCallCollector()
        collector.on_lm_start(call_id="test-1")
        assert "test-1" in collector._call_starts

    def test_on_lm_end_captures_call(self):
        collector = LmCallCollector()
        collector.on_lm_start(call_id="test-1")
        collector.on_lm_end(
            call_id="test-1",
            outputs={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "hello"}],
                "outputs": "world",
                "input_tokens": 10,
                "output_tokens": 5,
            },
        )

        assert len(collector.calls) == 1
        record = collector.calls[0]
        assert record.model == "gpt-4"
        assert record.input_tokens == 10
        assert record.output_tokens == 5
        assert record.latency_ms > 0

    def test_on_lm_end_without_start_sets_zero_latency(self):
        """If on_lm_start was never called for a call_id, latency should be 0."""
        collector = LmCallCollector()
        collector.on_lm_end(call_id="unknown-id", outputs={"model": "test"})

        assert len(collector.calls) == 1
        assert collector.calls[0].latency_ms == 0.0

    def test_on_lm_end_with_exception(self):
        collector = LmCallCollector()
        collector.on_lm_start(call_id="test-1")
        collector.on_lm_end(
            call_id="test-1",
            outputs=None,
            exception=RuntimeError("API error"),
        )

        assert len(collector.calls) == 1
        assert "API error" in collector.calls[0].error

    def test_on_lm_end_with_none_outputs(self):
        """None outputs should not crash the collector."""
        collector = LmCallCollector()
        collector.on_lm_start(call_id="test-1")
        collector.on_lm_end(call_id="test-1", outputs=None)

        assert len(collector.calls) == 1
        assert collector.calls[0].model == ""
        assert collector.calls[0].input_tokens == 0

    def test_multiple_calls_captured_in_order(self):
        collector = LmCallCollector()
        for i in range(3):
            call_id = f"call-{i}"
            collector.on_lm_start(call_id=call_id)
            collector.on_lm_end(call_id=call_id, outputs={"model": f"model-{i}"})

        assert len(collector.calls) == 3
        assert collector.calls[0].model == "model-0"
        assert collector.calls[2].model == "model-2"

    def test_cleans_up_call_starts_on_end(self):
        """on_lm_end should remove the call_id from _call_starts to prevent leaks."""
        collector = LmCallCollector()
        collector.on_lm_start(call_id="test-1")
        assert "test-1" in collector._call_starts

        collector.on_lm_end(call_id="test-1", outputs={})
        assert "test-1" not in collector._call_starts


# ============================================================================
# flush_lm_calls
# ============================================================================


class TestFlushLmCalls:
    def test_empty_collector_returns_zero_stats(self):
        collector = LmCallCollector()
        stats = flush_lm_calls(collector, "test_activity")

        assert stats.flushed == 0
        assert stats.errors == 0

    @patch("unlock_llm_gateway.logger.get_sync_engine")
    def test_flushes_records_to_db(self, mock_get_engine):
        mock_conn = MagicMock()
        mock_get_engine.return_value.begin.return_value.__enter__ = MagicMock(
            return_value=mock_conn,
        )
        mock_get_engine.return_value.begin.return_value.__exit__ = MagicMock(
            return_value=False,
        )

        collector = LmCallCollector()
        collector.calls.append(LmCallRecord(model="gpt-4", prompt_messages="test1"))
        collector.calls.append(LmCallRecord(model="gpt-4", prompt_messages="test2"))

        stats = flush_lm_calls(collector, "translate_query")

        assert stats.flushed == 2
        assert stats.errors == 0
        # Should use a single batch insert, not row-by-row
        assert mock_conn.execute.call_count == 1

    @patch("unlock_llm_gateway.logger.get_sync_engine")
    def test_connection_error_reports_all_as_errors(self, mock_get_engine):
        mock_get_engine.return_value.begin.side_effect = RuntimeError("connection refused")

        collector = LmCallCollector()
        collector.calls.append(LmCallRecord(model="test"))

        stats = flush_lm_calls(collector, "test")

        assert stats.errors == 1
        assert "connection" in stats.error_messages[0].lower()

    @patch("unlock_llm_gateway.logger.get_sync_engine")
    def test_sets_activity_name_on_all_records(self, mock_get_engine):
        mock_conn = MagicMock()
        mock_get_engine.return_value.begin.return_value.__enter__ = MagicMock(
            return_value=mock_conn,
        )
        mock_get_engine.return_value.begin.return_value.__exit__ = MagicMock(
            return_value=False,
        )

        collector = LmCallCollector()
        collector.calls.append(LmCallRecord(model="gpt-4"))

        flush_lm_calls(collector, "analyze_data")

        # Verify the insert was called with the correct activity_name
        insert_call = mock_conn.execute.call_args
        records = insert_call[0][1]  # second positional arg = list of dicts
        assert all(r["activity_name"] == "analyze_data" for r in records)
