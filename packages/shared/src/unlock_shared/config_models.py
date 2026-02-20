"""Config Access boundary models — the contract between Data Manager and Config Access.

These types cross the Temporal activity boundary. Workflows in the Data Manager
create them as arguments; activities in Config Access receive and return them.

Design choices:
  - Domain objects (SchemaDefinition, PipelineDefinition, ViewDefinition) are
    storage-agnostic. They serialize to JSON for Redis but would work identically
    with PostgreSQL or any document store.
  - Every field is explicitly typed — no dict/Any placeholders.
  - Request/Result pairs follow the same pattern as source_models.py and data_models.py.
  - All Results extend PlatformResult for consistent success/failure handling.
  - Business verbs pass the Righting Software test: "If I switched from Redis to
    PostgreSQL, would this name still make sense?"
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from unlock_shared.models import PlatformResult

# ============================================================================
# Domain objects — stored as JSON in Redis
# ============================================================================


class FieldMapping(BaseModel):
    """Maps a source field to a target field with optional transformation."""

    source_field: str
    target_field: str
    transform: str | None = None  # lowercase, trim, parse_date, etc.
    default_value: str | None = None


class TransformRule(BaseModel):
    """A single rule in a transformation pipeline."""

    rule_type: str  # map, filter, aggregate, enrich, deduplicate
    config: dict[str, str | int | float | bool | None] = {}
    order: int = 0


class FunnelStage(BaseModel):
    """A stage in an analysis funnel."""

    name: str
    description: str | None = None
    filter_expression: str | None = None
    order: int = 0


class SchemaDefinition(BaseModel):
    """A user-defined analysis/funnel schema — versioned and immutable per version."""

    id: str = ""
    name: str
    description: str | None = None
    version: int = 1
    status: str = "draft"  # draft, active, archived
    schema_type: str = "analysis"  # analysis, funnel, report
    fields: list[FieldMapping] = []
    funnel_stages: list[FunnelStage] = []
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None


class PipelineDefinition(BaseModel):
    """A transformation pipeline registered for a source type."""

    id: str = ""
    name: str
    description: str | None = None
    version: int = 1
    status: str = "draft"  # draft, active, disabled
    source_type: str  # which source type this pipeline processes
    transform_rules: list[TransformRule] = []
    schedule_cron: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None


class ViewDefinition(BaseModel):
    """A configured visualization/data view with sharing and lineage."""

    id: str = ""
    name: str
    description: str | None = None
    schema_id: str = ""
    status: str = "draft"  # draft, active, archived
    share_token: str | None = None
    filters: dict[str, str | int | float | bool | None] = {}
    layout_config: dict[str, str | int | float | bool | None] = {}
    cloned_from: str | None = None  # parent view ID for lineage
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None


class ViewPermission(BaseModel):
    """Access permission on a view for a principal."""

    view_id: str
    principal_id: str
    principal_type: str = "user"  # user, role, org
    permission: str = "read"  # read, write, admin
    granted_at: datetime | None = None
    granted_by: str | None = None


# ============================================================================
# Activity Request/Result Pairs (9)
# ============================================================================


class PublishSchemaRequest(BaseModel):
    """Input for publish_schema: validate, version, store a schema definition."""

    name: str
    description: str | None = None
    schema_type: str = "analysis"
    fields: list[FieldMapping] = []
    funnel_stages: list[FunnelStage] = []
    created_by: str | None = None


class PublishSchemaResult(PlatformResult):
    """Result of publish_schema."""

    schema_id: str = ""
    version: int = 0


class DefinePipelineRequest(BaseModel):
    """Input for define_pipeline: register transformation pipeline for a source type."""

    name: str
    description: str | None = None
    source_type: str
    transform_rules: list[TransformRule] = []
    schedule_cron: str | None = None
    created_by: str | None = None


class DefinePipelineResult(PlatformResult):
    """Result of define_pipeline."""

    pipeline_id: str = ""
    version: int = 0


class ActivateViewRequest(BaseModel):
    """Input for activate_view: create/update view, validate schema ref, generate share token."""

    name: str
    description: str | None = None
    schema_id: str
    filters: dict[str, str | int | float | bool | None] = {}
    layout_config: dict[str, str | int | float | bool | None] = {}
    created_by: str | None = None


class ActivateViewResult(PlatformResult):
    """Result of activate_view."""

    view_id: str = ""
    share_token: str = ""


class RetrieveViewRequest(BaseModel):
    """Input for retrieve_view: assemble complete view by share token."""

    share_token: str


class RetrieveViewResult(PlatformResult):
    """Result of retrieve_view: view + schema + permissions."""

    view: dict[str, Any] | None = None
    schema_def: dict[str, Any] | None = None
    permissions: list[dict[str, Any]] = []


class GrantAccessRequest(BaseModel):
    """Input for grant_access: add permission on a view for a principal."""

    view_id: str
    principal_id: str
    principal_type: str = "user"
    permission: str = "read"
    granted_by: str | None = None


class GrantAccessResult(PlatformResult):
    """Result of grant_access."""

    granted: bool = False


class RevokeAccessRequest(BaseModel):
    """Input for revoke_access: remove permission, cascade to cloned child views."""

    view_id: str
    principal_id: str


class RevokeAccessResult(PlatformResult):
    """Result of revoke_access."""

    revoked_count: int = 0


class CloneViewRequest(BaseModel):
    """Input for clone_view: deep copy with lineage tracking."""

    source_view_id: str
    new_name: str
    created_by: str | None = None


class CloneViewResult(PlatformResult):
    """Result of clone_view."""

    view_id: str = ""
    share_token: str = ""


class ArchiveSchemaRequest(BaseModel):
    """Input for archive_schema: soft delete, check dependent views."""

    schema_id: str


class ArchiveSchemaResult(PlatformResult):
    """Result of archive_schema."""

    archived: bool = False
    dependent_view_count: int = 0


class SurveyConfigsRequest(BaseModel):
    """Input for survey_configs: list/search schemas, pipelines, or views."""

    config_type: str  # schema, pipeline, view
    status: str | None = None
    name_pattern: str | None = None
    limit: int = 100
    offset: int = 0


class SurveyConfigsResult(PlatformResult):
    """Result of survey_configs."""

    items: list[dict[str, Any]] = []
    total_count: int = 0
    has_more: bool = False
