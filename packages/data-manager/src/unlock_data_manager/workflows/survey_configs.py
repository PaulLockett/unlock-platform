"""SurveyConfigsWorkflow: list/search schemas, pipelines, or views.

Single-step dispatch to the survey_configs activity on Config Access.
Used by /api/configs (list schemas/pipelines) and /api/views (list views).
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_config_access.activities import survey_configs
    from unlock_shared.config_models import SurveyConfigsRequest, SurveyConfigsResult
    from unlock_shared.task_queues import CONFIG_ACCESS_QUEUE


@workflow.defn
class SurveyConfigsWorkflow:
    """List/search configuration objects (schemas, pipelines, views)."""

    @workflow.run
    async def run(self, request: SurveyConfigsRequest) -> SurveyConfigsResult:
        return await workflow.execute_activity(
            survey_configs,
            request,
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )
