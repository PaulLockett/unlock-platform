"""ScheduleHarvestWorkflow: dispatch schedule operations to Scheduler activities.

The Canvas API routes call this workflow on DATA_MANAGER_QUEUE. It routes
the request to the appropriate Scheduler activity on SCHEDULER_QUEUE.

This keeps the pattern: Clients → Manager → Utility (closed architecture).
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_scheduler.activities import (
        cancel_harvest,
        describe_harvest,
        list_harvests,
        pause_harvest,
        register_harvest,
        resume_harvest,
    )
    from unlock_shared.scheduler_models import (
        CancelHarvestRequest,
        DescribeHarvestRequest,
        ListHarvestsRequest,
        PauseHarvestRequest,
        RegisterHarvestRequest,
        ResumeHarvestRequest,
    )
    from unlock_shared.task_queues import SCHEDULER_QUEUE


@workflow.defn
class ScheduleHarvestWorkflow:
    """Routes schedule operations to Scheduler activities."""

    @workflow.run
    async def run(self, request: dict) -> dict:
        action = request.get("action", "")

        if action == "register":
            return await self._register(request)
        elif action == "pause":
            return await self._pause(request)
        elif action == "resume":
            return await self._resume(request)
        elif action == "cancel":
            return await self._cancel(request)
        elif action == "describe":
            return await self._describe(request)
        elif action == "list":
            return await self._list()
        else:
            return {"success": False, "message": f"Unknown action: {action}"}

    async def _register(self, request: dict) -> dict:
        req = RegisterHarvestRequest(
            source_name=request["source_name"],
            cron_expression=request["cron_expression"],
            time_zone=request.get("time_zone", "America/Chicago"),
            note=request.get("note", ""),
            source_type=request.get("source_type", ""),
            resource_type=request.get("resource_type", "posts"),
            channel_key=request.get("channel_key"),
            auth_env_var=request.get("auth_env_var"),
            base_url=request.get("base_url"),
            config_json=request.get("config_json"),
            max_pages=request.get("max_pages", 100),
        )
        result = await workflow.execute_activity(
            register_harvest,
            req,
            task_queue=SCHEDULER_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )
        return result.model_dump()

    async def _pause(self, request: dict) -> dict:
        result = await workflow.execute_activity(
            pause_harvest,
            PauseHarvestRequest(
                source_name=request["source_name"],
                note=request.get("note", "Paused by admin"),
            ),
            task_queue=SCHEDULER_QUEUE,
            start_to_close_timeout=timedelta(seconds=15),
        )
        return result.model_dump()

    async def _resume(self, request: dict) -> dict:
        result = await workflow.execute_activity(
            resume_harvest,
            ResumeHarvestRequest(
                source_name=request["source_name"],
                note=request.get("note", "Resumed by admin"),
            ),
            task_queue=SCHEDULER_QUEUE,
            start_to_close_timeout=timedelta(seconds=15),
        )
        return result.model_dump()

    async def _cancel(self, request: dict) -> dict:
        result = await workflow.execute_activity(
            cancel_harvest,
            CancelHarvestRequest(source_name=request["source_name"]),
            task_queue=SCHEDULER_QUEUE,
            start_to_close_timeout=timedelta(seconds=15),
        )
        return result.model_dump()

    async def _describe(self, request: dict) -> dict:
        result = await workflow.execute_activity(
            describe_harvest,
            DescribeHarvestRequest(source_name=request["source_name"]),
            task_queue=SCHEDULER_QUEUE,
            start_to_close_timeout=timedelta(seconds=15),
        )
        return result.model_dump()

    async def _list(self) -> dict:
        result = await workflow.execute_activity(
            list_harvests,
            ListHarvestsRequest(),
            task_queue=SCHEDULER_QUEUE,
            start_to_close_timeout=timedelta(seconds=15),
        )
        return result.model_dump()
