"""Scheduler boundary models — the contract between Data Manager and Scheduler.

These types cross the Temporal activity boundary. Workflows in the Data Manager
create them as arguments; activities in the Scheduler receive and return them.

Design choices:
  - Business verbs pass the Righting Software test: "If I switched from Temporal
    Schedules to cron jobs, would this name still make sense?" Yes — register,
    pause, resume, cancel, describe, list are all schedule-agnostic.
  - Schedule IDs are deterministic: harvest-{source_name}. Callers don't need to
    track opaque IDs — the source name IS the lookup key.
  - Results extend PlatformResult for consistent success/failure handling.
  - Time zone defaults to "America/Chicago" (Alabama's time zone).
"""

from __future__ import annotations

from pydantic import BaseModel

from unlock_shared.models import PlatformResult

# ============================================================================
# Activity Request/Result Pairs (6)
# ============================================================================


class RegisterHarvestRequest(BaseModel):
    """Input for register_harvest: create a recurring schedule for a data source."""

    source_name: str
    cron_expression: str
    time_zone: str = "America/Chicago"
    note: str = ""


class RegisterHarvestResult(PlatformResult):
    """Result of register_harvest."""

    schedule_id: str = ""


class PauseHarvestRequest(BaseModel):
    """Input for pause_harvest: temporarily stop a recurring schedule."""

    source_name: str
    note: str = "Paused by platform"


class PauseHarvestResult(PlatformResult):
    """Result of pause_harvest."""

    schedule_id: str = ""


class ResumeHarvestRequest(BaseModel):
    """Input for resume_harvest: restart a paused schedule."""

    source_name: str
    note: str = "Resumed by platform"


class ResumeHarvestResult(PlatformResult):
    """Result of resume_harvest."""

    schedule_id: str = ""


class CancelHarvestRequest(BaseModel):
    """Input for cancel_harvest: permanently delete a schedule."""

    source_name: str


class CancelHarvestResult(PlatformResult):
    """Result of cancel_harvest."""

    schedule_id: str = ""


class DescribeHarvestRequest(BaseModel):
    """Input for describe_harvest: get current status and run history."""

    source_name: str


class DescribeHarvestResult(PlatformResult):
    """Result of describe_harvest: schedule status, next run, recent runs."""

    schedule_id: str = ""
    is_paused: bool = False
    cron_expression: str = ""
    next_run_time: str = ""
    recent_runs: list[dict[str, str]] = []


class ListHarvestsRequest(BaseModel):
    """Input for list_harvests: enumerate all active schedules."""


class ListHarvestsResult(PlatformResult):
    """Result of list_harvests: all schedules with summary metadata."""

    schedules: list[dict[str, str | bool]] = []
