"""Transform Engine boundary models — the contract between Data Manager and Transform Engine.

These types cross the Temporal child-workflow boundary. The Data Manager starts
a TransformWorkflow as a child workflow, passing identifiers (not data payloads).
The engine fetches what it needs from RA, transforms locally, pushes results back
to RA, and returns a lightweight pointer.

Design choices:
  - TransformRequest carries identifiers (source_type, pipeline_run_id), not records.
    The engine pulls records from Data Access and pipeline definitions from Config Access.
  - TransformPointer is the return value — counts and IDs, never raw data.
  - ValidatePipelineRequest/Result is for dry-run validation of transform rules
    without executing the full pipeline.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from unlock_shared.models import PlatformResult


class TransformRequest(BaseModel):
    """Manager passes identifiers — engine fetches, transforms, stores, returns pointer."""

    source_type: str
    pipeline_run_id: str | None = None


class TransformPointer(PlatformResult):
    """Pointer returned to Manager — no data payload, just references."""

    pipeline_run_id: str = ""
    source_type: str = ""
    records_in: int = 0
    records_out: int = 0
    records_stored: int = 0
    rules_applied: int = 0


class ValidatePipelineRequest(BaseModel):
    """Input for validate_pipeline: dry-run validation of transform rules."""

    transform_rules: list[dict[str, Any]]
    field_mappings: list[dict[str, str | None]] = []
    sample_record: dict[str, Any] | None = None


class ValidatePipelineResult(PlatformResult):
    """Result of validate_pipeline: validation report without executing the pipeline."""

    is_valid: bool = False
    errors: list[str] = []
    warnings: list[str] = []
