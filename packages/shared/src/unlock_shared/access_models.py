"""Access Control Engine boundary models — contract between Data Manager and Access Engine.

These types cross the Temporal child-workflow boundary. The Data Manager starts
CheckAccessWorkflow or EvaluatePermissionsWorkflow, passing identifiers (share_token,
principal_id). The engine fetches permissions from Config Access, evaluates locally,
and returns lightweight decision pointers.

Volatility encapsulated: Who can access what data, under what conditions.
Permission models evolve independently from data.
"""

from __future__ import annotations

from pydantic import BaseModel

from unlock_shared.models import PlatformResult


class CheckAccessRequest(BaseModel):
    """Manager passes share_token — engine fetches view + permissions."""

    share_token: str
    principal_id: str
    principal_type: str = "user"
    required_permission: str = "read"


class CheckAccessPointer(PlatformResult):
    """Lightweight decision pointer — no data to store."""

    allowed: bool = False
    view_id: str = ""
    matched_permission: str = ""
    reason: str = ""


class EvaluatePermissionsRequest(BaseModel):
    """Manager passes share_token — engine assembles effective permissions."""

    share_token: str
    principal_id: str
    principal_type: str = "user"
    resource_type: str | None = None


class EvaluatePermissionsPointer(PlatformResult):
    """Pointer to permissions — references views in Config Access."""

    view_ids: list[str] = []
    permission_levels: dict[str, str] = {}
    total_count: int = 0
