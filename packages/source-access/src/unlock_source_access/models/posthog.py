"""Typed models for PostHog API responses.

PostHog is our product analytics platform. We fetch events and person
profiles for understanding user behavior on Unlock Alabama web properties.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class PostHogEvent(BaseModel):
    """A single analytics event from PostHog."""

    id: str = ""
    event: str = ""
    distinct_id: str = ""
    timestamp: datetime | None = None
    properties: dict[str, Any] = {}
    elements: list[dict[str, Any]] = []


class PostHogPerson(BaseModel):
    """A person profile from PostHog."""

    id: str = ""
    distinct_ids: list[str] = []
    properties: dict[str, Any] = {}
    created_at: datetime | None = None
    is_identified: bool = False


class PostHogQueryResult(BaseModel):
    """Result from PostHog's query API (HogQL)."""

    columns: list[str] = []
    results: list[list[Any]] = []
    types: list[str] = []
    hasMore: bool = False
