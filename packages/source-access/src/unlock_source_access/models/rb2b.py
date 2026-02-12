"""Typed models for RB2B API responses.

RB2B provides B2B visitor identification — identifying companies and
individuals visiting our web properties. It has two modes:
  1. API enrichment (IP→email, email→person, LinkedIn→profile)
  2. File dump consumption (CSV/JSON exports from dashboard)

Credit-based pricing means the connector should track usage.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RB2BCompany(BaseModel):
    """Company information from RB2B enrichment."""

    name: str = ""
    domain: str = ""
    industry: str = ""
    employee_count: int = 0
    revenue_range: str = ""
    linkedin_url: str = ""
    location: str = ""


class RB2BPerson(BaseModel):
    """Individual visitor information from RB2B."""

    id: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    title: str = ""
    linkedin_url: str = ""
    company: RB2BCompany = RB2BCompany()
    page_views: list[dict[str, Any]] = []
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    visit_count: int = 0


class RB2BWebhookPayload(BaseModel):
    """Payload from an RB2B webhook push (for future webhook receiver)."""

    event_type: str = ""
    person: RB2BPerson = RB2BPerson()
    timestamp: datetime | None = None
    metadata: dict[str, Any] = {}
