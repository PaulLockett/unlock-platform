"""Pydantic base models shared across components.

These serve as the contract types that flow between workflows and activities.
Using Pydantic gives us automatic validation at component boundaries — if a
workflow sends bad data to an activity, it fails fast with a clear error
rather than propagating garbage downstream.
"""

from pydantic import BaseModel


class PlatformResult(BaseModel):
    """Standard result envelope returned by activities.

    Every activity returns this (or a subclass) so workflows have a consistent
    interface for checking success/failure without catching exceptions for
    expected business failures.
    """

    success: bool
    message: str
    data: dict[str, str | int | float | bool | None] | None = None
