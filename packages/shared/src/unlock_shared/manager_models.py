"""Data Manager boundary models — the contract between Clients and the Data Manager.

These types cross the Temporal workflow boundary. Clients (Analytics Canvas,
API endpoints) create Request objects; the Data Manager returns Result objects.

Four workflow pairs mirror the Data Manager's four orchestration responsibilities:
  - Ingest:    raw data → transform → store
  - Query:     access check → retrieve → return
  - Configure: polymorphic dispatch to schema/pipeline/view config
  - Share:     access check → grant permission

Design choices:
  - All Result types extend PlatformResult for consistent success/message interface.
  - ConfigureRequest uses config_type discriminator + union of optional fields rather
    than separate request types. The Manager routes internally — Clients don't need
    to know which Config Access activity handles which config type.
  - IngestRequest carries connection parameters (auth_env_var, base_url) so the
    Manager can build a FetchRequest for Source Access without round-tripping to
    Config Access for simple ingestion.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from unlock_shared.models import PlatformResult

# ============================================================================
# Ingest: raw data acquisition → transform → store
# ============================================================================


class IngestRequest(BaseModel):
    """Parameters to start the ingestion pipeline for a data source."""

    source_name: str
    source_type: str
    resource_type: str = "posts"
    channel_key: str | None = None
    auth_env_var: str | None = None
    base_url: str | None = None
    config_json: str | None = None
    since: datetime | None = None
    max_pages: int = 100


class IngestResult(PlatformResult):
    """Outcome of a complete ingestion run — counts at each stage."""

    source_name: str = ""
    records_fetched: int = 0
    records_stored: int = 0
    records_transformed: int = 0
    pipeline_run_id: str = ""


# ============================================================================
# Query: access-controlled data retrieval
# ============================================================================


class QueryRequest(BaseModel):
    """Parameters for a data query through a shared view."""

    share_token: str
    user_id: str
    user_type: str = "user"
    channel_key: str | None = None
    engagement_type: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    limit: int = 100
    offset: int = 0


class QueryResult(PlatformResult):
    """Result of a data query — records plus pagination metadata."""

    records: list[dict[str, Any]] = []
    total_count: int = 0
    has_more: bool = False
    view_name: str = ""
    schema_id: str = ""


# ============================================================================
# Configure: polymorphic config dispatch (schema / pipeline / view)
# ============================================================================


class ConfigureRequest(BaseModel):
    """Polymorphic configuration request — config_type selects the branch.

    Only the fields relevant to the selected config_type need to be populated.
    The Manager validates and routes internally.
    """

    config_type: str  # "schema", "pipeline", or "view"

    # Common fields
    name: str = ""
    description: str | None = None
    created_by: str | None = None

    # Schema-specific
    schema_type: str = "analysis"
    fields: list[dict[str, Any]] = []
    funnel_stages: list[dict[str, Any]] = []

    # Pipeline-specific
    source_type: str = ""
    transform_rules: list[dict[str, Any]] = []
    schedule_cron: str | None = None

    # View-specific
    schema_id: str = ""
    filters: dict[str, Any] = {}
    layout_config: dict[str, Any] = {}
    visibility: str = "public"
    # For view updates: pass existing IDs to update instead of create
    view_id: str | None = None
    share_token: str | None = None


class ConfigureResult(PlatformResult):
    """Outcome of a configuration operation — resource reference."""

    config_type: str = ""
    resource_id: str = ""
    version: int = 0
    share_token: str = ""


# ============================================================================
# Share: permission grant through access control
# ============================================================================


class ShareRequest(BaseModel):
    """Parameters to grant access on a shared view."""

    share_token: str
    granter_id: str
    recipient_id: str
    recipient_type: str = "user"
    permission: str = "read"


class ShareResult(PlatformResult):
    """Outcome of a share operation — confirms the grant."""

    view_id: str = ""
    share_token: str = ""
    granted_permission: str = ""
