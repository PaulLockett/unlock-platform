"""Tests for DSPy LM client configuration."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from unlock_llm_gateway.client import get_lm


class TestGetLm:
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False)
    def test_missing_api_key_raises(self):
        """get_lm must raise RuntimeError if OPENROUTER_API_KEY is not set."""
        with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
            get_lm()

    @patch("unlock_llm_gateway.client.dspy.LM")
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}, clear=False)
    def test_default_model(self, mock_lm_class):
        """Empty model string should fall back to DEFAULT_MODEL."""
        from unlock_shared.llm_models import DEFAULT_MODEL

        get_lm("")

        mock_lm_class.assert_called_once_with(
            model=DEFAULT_MODEL,
            api_key="test-key-123",
            cache=False,
        )

    @patch("unlock_llm_gateway.client.dspy.LM")
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}, clear=False)
    def test_model_override(self, mock_lm_class):
        """Explicit model string should be used instead of DEFAULT_MODEL."""
        get_lm("openrouter/openai/gpt-4o")

        mock_lm_class.assert_called_once_with(
            model="openrouter/openai/gpt-4o",
            api_key="test-key-123",
            cache=False,
        )

    @patch("unlock_llm_gateway.client.dspy.LM")
    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key-123"}, clear=False)
    def test_cache_disabled(self, mock_lm_class):
        """DSPy cache must be disabled — Temporal handles retries, not DSPy."""
        get_lm()

        call_kwargs = mock_lm_class.call_args[1]
        assert call_kwargs["cache"] is False
