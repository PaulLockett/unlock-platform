"""Scheduler activities — 6 business verb operations for Temporal Schedule management.

Run on SCHEDULER_QUEUE. Each activity connects to Temporal as a client and
manages schedules via the Schedule API. This is the correct pattern because:
  - Workflow code must be deterministic — it cannot make network calls directly.
  - Activities provide retry, timeout, and heartbeat for free.
  - The Data Manager dispatches schedule operations as activities, keeping
    orchestration logic in the workflow and I/O in the activity.

Business verbs follow the Righting Software test: "If I switched from Temporal
Schedules to cron jobs, would this operation name still make sense?"

Schedule IDs are deterministic: harvest-{normalized_source_name}. This eliminates
the need for a lookup table — callers pass source_name, we derive the ID.
"""

from __future__ import annotations

from temporalio import activity
from temporalio.client import (
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleSpec,
    ScheduleState,
)
from temporalio.service import RPCError, RPCStatusCode
from unlock_shared.scheduler_models import (
    CancelHarvestRequest,
    CancelHarvestResult,
    DescribeHarvestRequest,
    DescribeHarvestResult,
    ListHarvestsRequest,
    ListHarvestsResult,
    PauseHarvestRequest,
    PauseHarvestResult,
    RegisterHarvestRequest,
    RegisterHarvestResult,
    ResumeHarvestRequest,
    ResumeHarvestResult,
)
from unlock_shared.task_queues import DATA_MANAGER_QUEUE
from unlock_shared.temporal_client import connect


def _schedule_id(source_name: str) -> str:
    """Derive a deterministic schedule ID from the source name.

    Normalizes to lowercase, strips whitespace, replaces spaces with hyphens.
    Example: "Alabama Census" → "harvest-alabama-census"
    """
    slug = source_name.strip().lower().replace(" ", "-")
    return f"harvest-{slug}"


@activity.defn
async def register_harvest(req: RegisterHarvestRequest) -> RegisterHarvestResult:
    """Create a recurring Temporal Schedule for a data source.

    Uses ScheduleActionStartWorkflow to reference "IngestWorkflow" by string,
    avoiding a circular import (scheduler → data-manager). The workflow won't
    execute unless a worker is listening on DATA_MANAGER_QUEUE.

    Idempotent: if the schedule already exists (ALREADY_EXISTS), returns success.
    """
    sid = _schedule_id(req.source_name)

    try:
        client = await connect()
        await client.create_schedule(
            id=sid,
            schedule=Schedule(
                action=ScheduleActionStartWorkflow(
                    "IngestWorkflow",
                    id=f"{sid}-run",
                    task_queue=DATA_MANAGER_QUEUE,
                ),
                spec=ScheduleSpec(
                    cron_expressions=[req.cron_expression],
                    time_zone_name=req.time_zone,
                ),
                state=ScheduleState(
                    note=req.note or f"Harvest schedule for {req.source_name}",
                ),
            ),
            memo={"source_name": req.source_name},
        )
        return RegisterHarvestResult(
            success=True,
            message=f"Schedule {sid} created",
            schedule_id=sid,
        )
    except RPCError as e:
        if e.status == RPCStatusCode.ALREADY_EXISTS:
            return RegisterHarvestResult(
                success=True,
                message=f"Schedule {sid} already exists (idempotent)",
                schedule_id=sid,
            )
        return RegisterHarvestResult(
            success=False,
            message=f"Failed to create schedule {sid}: {e}",
            schedule_id=sid,
        )
    except Exception as e:
        return RegisterHarvestResult(
            success=False,
            message=f"Failed to create schedule {sid}: {e}",
            schedule_id=sid,
        )


@activity.defn
async def pause_harvest(req: PauseHarvestRequest) -> PauseHarvestResult:
    """Pause an active harvest schedule. Temporal remembers the pause state."""
    sid = _schedule_id(req.source_name)

    try:
        client = await connect()
        handle = client.get_schedule_handle(sid)
        await handle.pause(note=req.note)
        return PauseHarvestResult(
            success=True,
            message=f"Schedule {sid} paused",
            schedule_id=sid,
        )
    except Exception as e:
        return PauseHarvestResult(
            success=False,
            message=f"Failed to pause schedule {sid}: {e}",
            schedule_id=sid,
        )


@activity.defn
async def resume_harvest(req: ResumeHarvestRequest) -> ResumeHarvestResult:
    """Resume a paused harvest schedule."""
    sid = _schedule_id(req.source_name)

    try:
        client = await connect()
        handle = client.get_schedule_handle(sid)
        await handle.unpause(note=req.note)
        return ResumeHarvestResult(
            success=True,
            message=f"Schedule {sid} resumed",
            schedule_id=sid,
        )
    except Exception as e:
        return ResumeHarvestResult(
            success=False,
            message=f"Failed to resume schedule {sid}: {e}",
            schedule_id=sid,
        )


@activity.defn
async def cancel_harvest(req: CancelHarvestRequest) -> CancelHarvestResult:
    """Permanently delete a harvest schedule from Temporal."""
    sid = _schedule_id(req.source_name)

    try:
        client = await connect()
        handle = client.get_schedule_handle(sid)
        await handle.delete()
        return CancelHarvestResult(
            success=True,
            message=f"Schedule {sid} deleted",
            schedule_id=sid,
        )
    except Exception as e:
        return CancelHarvestResult(
            success=False,
            message=f"Failed to delete schedule {sid}: {e}",
            schedule_id=sid,
        )


@activity.defn
async def describe_harvest(req: DescribeHarvestRequest) -> DescribeHarvestResult:
    """Get current status, next run time, and recent run history for a schedule.

    Extracts from ScheduleDescription:
      - is_paused: from schedule.state.paused
      - cron_expression: from schedule.spec.cron_expressions[0]
      - next_run_time: from info.next_action_times[0] (ISO format)
      - recent_runs: from info.recent_actions (workflow_id + started_at)
    """
    sid = _schedule_id(req.source_name)

    try:
        client = await connect()
        handle = client.get_schedule_handle(sid)
        desc = await handle.describe()

        # Extract cron expression
        cron = ""
        if desc.schedule.spec.cron_expressions:
            cron = desc.schedule.spec.cron_expressions[0]

        # Extract next run time
        next_run = ""
        if desc.info.next_action_times:
            next_run = desc.info.next_action_times[0].isoformat()

        # Extract recent runs
        recent: list[dict[str, str]] = []
        for action_result in desc.info.recent_actions:
            run: dict[str, str] = {
                "started_at": action_result.started_at.isoformat(),
            }
            if hasattr(action_result.action, "workflow_id"):
                run["workflow_id"] = action_result.action.workflow_id
            recent.append(run)

        return DescribeHarvestResult(
            success=True,
            message=f"Schedule {sid} described",
            schedule_id=sid,
            is_paused=desc.schedule.state.paused,
            cron_expression=cron,
            next_run_time=next_run,
            recent_runs=recent,
        )
    except Exception as e:
        return DescribeHarvestResult(
            success=False,
            message=f"Failed to describe schedule {sid}: {e}",
            schedule_id=sid,
        )


@activity.defn
async def list_harvests(req: ListHarvestsRequest) -> ListHarvestsResult:
    """Enumerate all harvest schedules in the Temporal namespace.

    Iterates client.list_schedules() and extracts summary metadata for each.
    Only includes schedules with IDs starting with "harvest-" (our convention).
    """
    try:
        client = await connect()
        schedules: list[dict[str, str | bool]] = []

        async for entry in await client.list_schedules():
            if not entry.id.startswith("harvest-"):
                continue

            info: dict[str, str | bool] = {
                "schedule_id": entry.id,
            }

            # Extract source_name from memo if available.
            # ScheduleListDescription.memo() is a method returning Mapping[str, Any].
            try:
                memo = entry.memo()
                source = memo.get("source_name", "")
                if source:
                    info["source_name"] = source
            except Exception:
                pass

            # Extract state from schedule if available
            if entry.schedule and entry.schedule.state:
                info["is_paused"] = entry.schedule.state.paused
                if entry.schedule.state.note:
                    info["note"] = entry.schedule.state.note

            # Extract cron from spec if available
            if entry.schedule and entry.schedule.spec and entry.schedule.spec.cron_expressions:
                info["cron_expression"] = entry.schedule.spec.cron_expressions[0]

            schedules.append(info)

        return ListHarvestsResult(
            success=True,
            message=f"Found {len(schedules)} harvest schedule(s)",
            schedules=schedules,
        )
    except Exception as e:
        return ListHarvestsResult(
            success=False,
            message=f"Failed to list schedules: {e}",
        )
