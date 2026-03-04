"""QueryWorkflow: access check → retrieve view → survey engagement data.

Three-step orchestration with a fail-fast access gate:
1. CheckAccessWorkflow (child workflow on Access Engine queue) — fail immediately
   if the user doesn't have read access. Don't fetch data for unauthorized users.
2. retrieve_view (Config Access activity) — get the view config + schema.
3. survey_engagement (Data Access activity) — fetch matching records.

Schema validation is intentionally absent from the query path. Validation happens
during configuration and ingestion — at read time, the data is already valid.
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_access_engine.workflows import CheckAccessWorkflow
    from unlock_config_access.activities import retrieve_view
    from unlock_data_access.activities import survey_engagement
    from unlock_shared.access_models import CheckAccessRequest
    from unlock_shared.config_models import RetrieveViewRequest
    from unlock_shared.data_models import SurveyEngagementRequest
    from unlock_shared.manager_models import QueryRequest, QueryResult
    from unlock_shared.task_queues import (
        ACCESS_ENGINE_QUEUE,
        CONFIG_ACCESS_QUEUE,
        DATA_ACCESS_QUEUE,
    )


@workflow.defn
class QueryWorkflow:
    """Access-controlled data retrieval through a shared view."""

    @workflow.run
    async def run(self, request: QueryRequest) -> QueryResult:
        # Step 1: Access check — fail fast if unauthorized
        access_result = await workflow.execute_child_workflow(
            CheckAccessWorkflow.run,
            CheckAccessRequest(
                share_token=request.share_token,
                principal_id=request.user_id,
                principal_type=request.user_type,
                required_permission="read",
            ),
            id=f"{workflow.info().workflow_id}-check-access",
            task_queue=ACCESS_ENGINE_QUEUE,
        )

        if not access_result.success or not access_result.allowed:
            return QueryResult(
                success=False,
                message=f"Access denied for '{request.user_id}': {access_result.reason}",
            )

        # Step 2: Retrieve view config + schema from Config Access
        view_result = await workflow.execute_activity(
            retrieve_view,
            RetrieveViewRequest(share_token=request.share_token),
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not view_result.success:
            return QueryResult(
                success=False,
                message=f"Failed to retrieve view: {view_result.message}",
            )

        # Extract view metadata for the result
        view_name = ""
        schema_id = ""
        if view_result.view:
            view_name = view_result.view.get("name", "")
            schema_id = view_result.view.get("schema_id", "")

        # Step 3: Survey engagement data from Data Access
        engagement_result = await workflow.execute_activity(
            survey_engagement,
            SurveyEngagementRequest(
                channel_key=request.channel_key,
                engagement_type=request.engagement_type,
                since=request.since,
                until=request.until,
                limit=request.limit,
                offset=request.offset,
            ),
            task_queue=DATA_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(minutes=2),
        )

        if not engagement_result.success:
            return QueryResult(
                success=False,
                message=f"Failed to fetch data: {engagement_result.message}",
            )

        return QueryResult(
            success=True,
            message=f"Retrieved {engagement_result.total_count} records from '{view_name}'",
            records=engagement_result.records,
            total_count=engagement_result.total_count,
            has_more=engagement_result.has_more,
            view_name=view_name,
            schema_id=schema_id,
        )
