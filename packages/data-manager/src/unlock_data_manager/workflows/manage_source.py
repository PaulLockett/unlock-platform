"""ManageSourceWorkflow: dispatch source identification and registration.

Two actions:
  action="identify" → calls identify_source activity on Source Access queue
  action="register" → calls register_source activity on Source Access queue

The frontend flow:
1. Admin names a source → Manager calls identify_source
2. If source exists → proceed to ingest via IngestWorkflow
3. If source is new → Manager calls register_source first
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_shared.source_models import (
        IdentifySourceRequest,
        IdentifySourceResult,
        RegisterSourceRequest,
        RegisterSourceResult,
    )
    from unlock_shared.task_queues import SOURCE_ACCESS_QUEUE
    from unlock_source_access.activities import identify_source, register_source


@workflow.defn
class ManageSourceWorkflow:
    """Dispatch source registry operations to Source Access."""

    @workflow.run
    async def run(self, request: dict) -> dict:
        action = request.get("action", "identify")

        if action == "identify":
            result = await workflow.execute_activity(
                identify_source,
                IdentifySourceRequest(
                    name=request.get("name"),
                    source_type=request.get("source_type"),
                ),
                task_queue=SOURCE_ACCESS_QUEUE,
                start_to_close_timeout=timedelta(seconds=30),
            )
            return result.model_dump()

        elif action == "register":
            result = await workflow.execute_activity(
                register_source,
                RegisterSourceRequest(
                    name=request["name"],
                    protocol=request["protocol"],
                    service=request.get("service", ""),
                    base_url=request.get("base_url", ""),
                    auth_method=request.get("auth_method", ""),
                    auth_env_var=request.get("auth_env_var", ""),
                    resource_type=request.get("resource_type", "posts"),
                    channel_key=request.get("channel_key", ""),
                    config=request.get("config", {}),
                ),
                task_queue=SOURCE_ACCESS_QUEUE,
                start_to_close_timeout=timedelta(seconds=30),
            )
            return result.model_dump()

        else:
            return {
                "success": False,
                "message": f"Unknown action: {action}. Use 'identify' or 'register'.",
            }
