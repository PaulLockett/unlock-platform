"""Tests for LLM Gateway activities — all 3 business verbs + hello shim.

Two test levels:

1. Activity tests — mock at the _run_* sync wrapper boundary.
   These test the async activity → result envelope contract.

2. Sync wrapper tests — mock at the program function + flush boundary.
   These test that flush runs in the sync wrapper (same thread as DSPy),
   that flush failures never break business logic, and that programs
   receive context from the wrapper (not their own inner context).

Pattern: unittest.mock.patch on the program functions and flush_lm_calls,
then call the activity directly and assert on the Result envelope.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from unlock_shared.llm_models import (
    AnalyzeDataRequest,
    DraftSchemaRequest,
    TranslateQueryRequest,
)

# ============================================================================
# translate_query — activity level
# ============================================================================


class TestTranslateQuery:
    @pytest.mark.asyncio
    async def test_translate_success(self):
        from unlock_llm_gateway.activities import translate_query

        mock_result = {"sql_query": "SELECT * FROM unlock.people", "explanation": "Gets all people"}

        with patch("unlock_llm_gateway.activities._run_translate", return_value=mock_result):
            req = TranslateQueryRequest(
                question="Show me all people",
                schema_context="unlock.people table with columns: id, display_name",
            )
            result = await translate_query(req)

        assert result.success is True
        assert result.sql_query == "SELECT * FROM unlock.people"
        assert result.explanation == "Gets all people"

    @pytest.mark.asyncio
    async def test_translate_failure(self):
        from unlock_llm_gateway.activities import translate_query

        with patch(
            "unlock_llm_gateway.activities._run_translate",
            side_effect=RuntimeError("API timeout"),
        ):
            req = TranslateQueryRequest(
                question="Show me all people",
                schema_context="unlock.people",
            )
            result = await translate_query(req)

        assert result.success is False
        assert "API timeout" in result.message

    @pytest.mark.asyncio
    async def test_translate_model_override(self):
        from unlock_llm_gateway.activities import translate_query

        mock_result = {"sql_query": "SELECT 1", "explanation": "test"}

        with patch(
            "unlock_llm_gateway.activities._run_translate",
            return_value=mock_result,
        ) as mock_run:
            req = TranslateQueryRequest(
                question="test",
                schema_context="test",
                model="openrouter/openai/gpt-4o",
            )
            await translate_query(req)

        # Verify the model override was passed through
        call_args = mock_run.call_args
        assert call_args[0][2] == "openrouter/openai/gpt-4o"


# ============================================================================
# draft_schema — activity level
# ============================================================================


class TestDraftSchema:
    @pytest.mark.asyncio
    async def test_draft_success(self):
        from unlock_llm_gateway.activities import draft_schema

        mock_result = {
            "schema_definition": '{"table": "events", "columns": ["id", "title"]}',
            "explanation": "Created events table",
        }

        with patch("unlock_llm_gateway.activities._run_draft", return_value=mock_result):
            req = DraftSchemaRequest(
                description="I need a table for community events",
                existing_context="We already have people and organizations tables",
            )
            result = await draft_schema(req)

        assert result.success is True
        assert "events" in result.schema_definition
        assert result.explanation == "Created events table"

    @pytest.mark.asyncio
    async def test_draft_failure(self):
        from unlock_llm_gateway.activities import draft_schema

        with patch(
            "unlock_llm_gateway.activities._run_draft",
            side_effect=RuntimeError("rate limited"),
        ):
            req = DraftSchemaRequest(description="test")
            result = await draft_schema(req)

        assert result.success is False
        assert "rate limited" in result.message

    @pytest.mark.asyncio
    async def test_draft_model_override(self):
        from unlock_llm_gateway.activities import draft_schema

        mock_result = {"schema_definition": "{}", "explanation": "test"}

        with patch(
            "unlock_llm_gateway.activities._run_draft", return_value=mock_result
        ) as mock_run:
            req = DraftSchemaRequest(
                description="test",
                model="openrouter/google/gemini-2.5-pro",
            )
            await draft_schema(req)

        call_args = mock_run.call_args
        assert call_args[0][2] == "openrouter/google/gemini-2.5-pro"


# ============================================================================
# analyze_data — activity level
# ============================================================================


class TestAnalyzeData:
    @pytest.mark.asyncio
    async def test_analyze_success(self):
        from unlock_llm_gateway.activities import analyze_data

        mock_result = {
            "answer": "There are 42 active organizations in Alabama.",
            "sql_queries": ["SELECT COUNT(*) FROM unlock.organizations WHERE is_active = true"],
            "trajectory": "Step 1: Listed tables. Step 2: Queried organizations.",
        }

        with patch("unlock_llm_gateway.activities._run_analyze", return_value=mock_result):
            req = AnalyzeDataRequest(question="How many active organizations are in Alabama?")
            result = await analyze_data(req)

        assert result.success is True
        assert "42" in result.answer
        assert len(result.sql_queries_executed) == 1
        assert result.trajectory != ""

    @pytest.mark.asyncio
    async def test_analyze_failure(self):
        from unlock_llm_gateway.activities import analyze_data

        with patch(
            "unlock_llm_gateway.activities._run_analyze",
            side_effect=RuntimeError("model unavailable"),
        ):
            req = AnalyzeDataRequest(question="test question")
            result = await analyze_data(req)

        assert result.success is False
        assert "model unavailable" in result.message

    @pytest.mark.asyncio
    async def test_analyze_model_override(self):
        from unlock_llm_gateway.activities import analyze_data

        mock_result = {"answer": "test", "sql_queries": [], "trajectory": ""}

        with patch(
            "unlock_llm_gateway.activities._run_analyze",
            return_value=mock_result,
        ) as mock_run:
            req = AnalyzeDataRequest(
                question="test",
                model="openrouter/anthropic/claude-opus-4",
            )
            await analyze_data(req)

        call_args = mock_run.call_args
        assert call_args[0][1] == "openrouter/anthropic/claude-opus-4"


# ============================================================================
# hello_llm_assess (backward compat shim)
# ============================================================================


class TestHelloLlmAssess:
    @pytest.mark.asyncio
    async def test_hello_shim(self):
        from unlock_llm_gateway.activities import hello_llm_assess

        result = await hello_llm_assess("test data quality check")
        assert "LLM assessment" in result
        assert "test data quality check" in result


# ============================================================================
# Sync wrapper tests — verify flush behavior and context delegation
# ============================================================================


class TestSyncWrappers:
    """Test that sync wrappers handle flush + context correctly.

    These wrappers are where the real safety contracts live:
    1. Flush runs in the same thread as DSPy (no event loop blocking)
    2. Flush failures never break business logic
    3. Programs inherit context from the wrapper (no inner dspy.context)
    """

    @patch("unlock_llm_gateway.activities.flush_lm_calls")
    @patch("unlock_llm_gateway.activities.run_translate_query")
    @patch("unlock_llm_gateway.activities.get_lm")
    def test_translate_wrapper_calls_flush(self, mock_get_lm, mock_run, mock_flush):
        """Flush must be called inside the sync wrapper (same thread)."""
        from unlock_llm_gateway.activities import _run_translate
        from unlock_llm_gateway.logger import LmCallCollector

        mock_run.return_value = {"sql_query": "SELECT 1", "explanation": "test"}
        collector = LmCallCollector()

        _run_translate("question", "schema", "model", collector)

        mock_flush.assert_called_once()

    @patch("unlock_llm_gateway.activities.flush_lm_calls", side_effect=RuntimeError("DB down"))
    @patch("unlock_llm_gateway.activities.run_translate_query")
    @patch("unlock_llm_gateway.activities.get_lm")
    def test_translate_wrapper_survives_flush_failure(self, mock_get_lm, mock_run, mock_flush):
        """If flush raises, the sync wrapper MUST still return the program result."""
        from unlock_llm_gateway.activities import _run_translate
        from unlock_llm_gateway.logger import LmCallCollector

        mock_run.return_value = {"sql_query": "SELECT 1", "explanation": "test"}
        collector = LmCallCollector()

        # Must not raise — flush failure is swallowed
        result = _run_translate("question", "schema", "model", collector)

        assert result == {"sql_query": "SELECT 1", "explanation": "test"}

    @patch("unlock_llm_gateway.activities.flush_lm_calls")
    @patch("unlock_llm_gateway.activities.run_translate_query")
    @patch("unlock_llm_gateway.activities.get_lm")
    def test_translate_wrapper_flushes_on_program_failure(self, mock_get_lm, mock_run, mock_flush):
        """Flush must run even when the program raises (via finally block)."""
        from unlock_llm_gateway.activities import _run_translate
        from unlock_llm_gateway.logger import LmCallCollector

        mock_run.side_effect = RuntimeError("LLM exploded")
        collector = LmCallCollector()

        with pytest.raises(RuntimeError, match="LLM exploded"):
            _run_translate("question", "schema", "model", collector)

        # Flush should still have been called despite the exception
        mock_flush.assert_called_once()

    @patch("unlock_llm_gateway.activities.flush_lm_calls")
    @patch("unlock_llm_gateway.activities.run_translate_query")
    @patch("unlock_llm_gateway.activities.get_lm")
    def test_translate_wrapper_calls_program_without_lm(self, mock_get_lm, mock_run, mock_flush):
        """Programs must NOT receive an LM param — they inherit the caller's context."""
        from unlock_llm_gateway.activities import _run_translate
        from unlock_llm_gateway.logger import LmCallCollector

        mock_run.return_value = {"sql_query": "SELECT 1", "explanation": "test"}
        collector = LmCallCollector()

        _run_translate("question", "schema", "model", collector)

        # Program should be called with (question, schema_context) only — no lm
        mock_run.assert_called_once_with("question", "schema")

    @patch("unlock_llm_gateway.activities.flush_lm_calls")
    @patch("unlock_llm_gateway.activities.run_draft_schema")
    @patch("unlock_llm_gateway.activities.get_lm")
    def test_draft_wrapper_survives_flush_failure(self, mock_get_lm, mock_run, mock_flush):
        from unlock_llm_gateway.activities import _run_draft
        from unlock_llm_gateway.logger import LmCallCollector

        mock_flush.side_effect = RuntimeError("DB down")
        mock_run.return_value = {"schema_definition": "{}", "explanation": "test"}
        collector = LmCallCollector()

        result = _run_draft("description", "context", "model", collector)

        assert result == {"schema_definition": "{}", "explanation": "test"}

    @patch("unlock_llm_gateway.activities.flush_lm_calls")
    @patch("unlock_llm_gateway.activities.run_draft_schema")
    @patch("unlock_llm_gateway.activities.get_lm")
    def test_draft_wrapper_calls_program_without_lm(self, mock_get_lm, mock_run, mock_flush):
        from unlock_llm_gateway.activities import _run_draft
        from unlock_llm_gateway.logger import LmCallCollector

        mock_run.return_value = {"schema_definition": "{}", "explanation": "test"}
        collector = LmCallCollector()

        _run_draft("description", "context", "model", collector)

        mock_run.assert_called_once_with("description", "context")

    @patch("unlock_llm_gateway.activities.flush_lm_calls")
    @patch("unlock_llm_gateway.activities.run_analyze_data")
    @patch("unlock_llm_gateway.activities.get_lm")
    def test_analyze_wrapper_survives_flush_failure(self, mock_get_lm, mock_run, mock_flush):
        from unlock_llm_gateway.activities import _run_analyze
        from unlock_llm_gateway.logger import LmCallCollector

        mock_flush.side_effect = RuntimeError("DB down")
        mock_run.return_value = {"answer": "42", "sql_queries": [], "trajectory": ""}
        collector = LmCallCollector()

        result = _run_analyze("question", "model", collector)

        assert result == {"answer": "42", "sql_queries": [], "trajectory": ""}

    @patch("unlock_llm_gateway.activities.flush_lm_calls")
    @patch("unlock_llm_gateway.activities.run_analyze_data")
    @patch("unlock_llm_gateway.activities.get_lm")
    def test_analyze_wrapper_calls_program_without_lm(self, mock_get_lm, mock_run, mock_flush):
        from unlock_llm_gateway.activities import _run_analyze
        from unlock_llm_gateway.logger import LmCallCollector

        mock_run.return_value = {"answer": "42", "sql_queries": [], "trajectory": ""}
        collector = LmCallCollector()

        _run_analyze("question", "model", collector)

        # Program should be called with (question, tools) only — no lm
        call_args = mock_run.call_args
        assert call_args[0][0] == "question"
        assert len(call_args[0]) == 2  # question + tools list, no lm
