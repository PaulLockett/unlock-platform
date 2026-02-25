"""DSPy LM configuration — single place where the OpenRouter connection lives.

get_lm() returns a configured dspy.LM instance for use in language programs.
Each activity call creates its own LM via dspy.context(lm=...) to avoid
global state between concurrent Temporal activities.

cache=False because Temporal handles retries, not DSPy. Caching at the DSPy
layer would hide failures from the retry/timeout machinery.
"""

from __future__ import annotations

import os

import dspy
from unlock_shared.llm_models import DEFAULT_MODEL


def get_lm(model: str = "") -> dspy.LM:
    """Return a configured DSPy LM instance backed by OpenRouter.

    Args:
        model: OpenRouter model identifier. Falls back to DEFAULT_MODEL if empty.

    Raises:
        RuntimeError: If OPENROUTER_API_KEY is not set.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY environment variable is not set. "
            "Set it to your OpenRouter API key."
        )

    resolved_model = model or DEFAULT_MODEL

    return dspy.LM(
        model=resolved_model,
        api_key=api_key,
        cache=False,
    )
