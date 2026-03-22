"""RetrieveViewWorkflow: assemble a complete view by share token.

Single-step dispatch to the retrieve_view activity on Config Access.
Returns the view definition, schema, and permissions in one call.
Used by /api/views/[shareToken] GET and PATCH.
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_config_access.activities import retrieve_view
    from unlock_shared.config_models import RetrieveViewRequest, RetrieveViewResult
    from unlock_shared.task_queues import CONFIG_ACCESS_QUEUE


@workflow.defn
class RetrieveViewWorkflow:
    """Retrieve a view's config, schema, and permissions by share token."""

    @workflow.run
    async def run(self, request: RetrieveViewRequest) -> RetrieveViewResult:
        return await workflow.execute_activity(
            retrieve_view,
            request,
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )
