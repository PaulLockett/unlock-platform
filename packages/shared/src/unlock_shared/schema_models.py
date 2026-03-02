"""Schema Engine boundary models — the contract between Data Manager and Schema Engine.

These types cross the Temporal child-workflow boundary. The Data Manager starts
GenerateMappingsWorkflow or ValidateSchemaWorkflow as child workflows, passing
identifiers. The engine discovers source schemas, generates mappings, detects
drift, and returns lightweight pointers.

Dual role:
  - Creates initial source→target mappings (GenerateMappingsWorkflow)
  - Validates existing data against schemas and detects drift (ValidateSchemaWorkflow)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from unlock_shared.models import PlatformResult


class GenerateMappingsRequest(BaseModel):
    """Manager passes source identifiers — engine discovers, generates, stores."""

    source_type: str
    source_config: dict[str, Any]
    target_schema_id: str | None = None


class GenerateMappingsPointer(PlatformResult):
    """Pointer returned to Manager — mappings stored in Config Access."""

    schema_id: str = ""
    version: int = 0
    mappings_generated: int = 0
    unmapped_source_fields: list[str] = []
    unmapped_target_fields: list[str] = []


class ValidateSchemaRequest(BaseModel):
    """Manager passes schema identifier — engine validates data against it."""

    schema_id: str
    source_type: str | None = None


class ValidateSchemaPointer(PlatformResult):
    """Pointer returned to Manager — drift results stored in Config Access."""

    schema_id: str = ""
    is_valid: bool = False
    valid_count: int = 0
    invalid_count: int = 0
    drift_detected: bool = False
    new_fields_count: int = 0
    missing_fields_count: int = 0


class DriftReport(BaseModel):
    """Drift detection results — produced by validate_and_detect_drift."""

    has_drift: bool = False
    new_fields: list[str] = []
    missing_fields: list[str] = []
    type_changes: list[dict[str, str]] = []
    sample_size: int = 0
