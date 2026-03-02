"""TransformWorkflow: child workflow dispatched by Data Manager.

Encapsulates the volatility of HOW raw data gets mapped, filtered, enriched, and
reshaped. Transformation rules evolve as new sources arrive with different structures,
but the orchestration layer (Data Manager) is unaffected.

Data flow:
  1. Manager passes identifiers (source_type, pipeline_run_id)
  2. Engine fetches pipeline definition from Config Access
  3. Engine fetches records from Data Access
  4. Engine applies transforms locally (pure computation)
  5. Engine pushes results back to Data Access
  6. Engine returns a pointer (pipeline_run_id, counts) — no data payload
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_config_access.activities import survey_configs
    from unlock_data_access.activities import (
        close_pipeline_run,
        open_pipeline_run,
        survey_engagement,
    )
    from unlock_shared.config_models import SurveyConfigsRequest
    from unlock_shared.data_models import (
        ClosePipelineRunRequest,
        OpenPipelineRunRequest,
        SurveyEngagementRequest,
    )
    from unlock_shared.task_queues import (
        CONFIG_ACCESS_QUEUE,
        DATA_ACCESS_QUEUE,
        TRANSFORM_ENGINE_QUEUE,
    )
    from unlock_shared.transform_models import TransformPointer, TransformRequest

    from unlock_transform_engine.activities import apply_transform_rules


@workflow.defn
class TransformWorkflow:
    """Fetches pipeline + records, transforms locally, pushes results to Data Access."""

    @workflow.run
    async def run(self, request: TransformRequest) -> TransformPointer:
        # Step 1: Open a pipeline run for tracking
        run_result = await workflow.execute_activity(
            open_pipeline_run,
            OpenPipelineRunRequest(
                source_key=request.source_type,
                workflow_run_id=workflow.info().workflow_id,
                resource_type="transform",
            ),
            task_queue=DATA_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )
        pipeline_run_id = request.pipeline_run_id or run_result.pipeline_run_id

        # Step 2: Find pipeline definition from Config Access
        configs_result = await workflow.execute_activity(
            survey_configs,
            SurveyConfigsRequest(
                config_type="pipeline",
                status="active",
            ),
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not configs_result.success:
            return TransformPointer(
                success=False,
                message=f"Failed to fetch pipeline configs: {configs_result.message}",
                pipeline_run_id=pipeline_run_id,
                source_type=request.source_type,
            )

        # Filter for matching source_type (deterministic — safe in workflow code)
        pipeline_def = None
        for item in configs_result.items:
            if item.get("source_type") == request.source_type:
                pipeline_def = item
                break

        if pipeline_def is None:
            return TransformPointer(
                success=False,
                message=f"No active pipeline found for source_type '{request.source_type}'",
                pipeline_run_id=pipeline_run_id,
                source_type=request.source_type,
            )

        # Step 3: Get records to transform from Data Access
        engagement_result = await workflow.execute_activity(
            survey_engagement,
            SurveyEngagementRequest(
                source_key=request.source_type,
            ),
            task_queue=DATA_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(minutes=2),
        )

        if not engagement_result.success:
            return TransformPointer(
                success=False,
                message=f"Failed to fetch records: {engagement_result.message}",
                pipeline_run_id=pipeline_run_id,
                source_type=request.source_type,
            )

        records_in = len(engagement_result.records)
        if records_in == 0:
            return TransformPointer(
                success=True,
                message="No records to transform",
                pipeline_run_id=pipeline_run_id,
                source_type=request.source_type,
                records_in=0,
                records_out=0,
            )

        # Step 4: Apply transforms (engine's own queue — pure computation)
        transform_input = {
            "records": engagement_result.records,
            "pipeline_def": pipeline_def,
        }
        transform_output = await workflow.execute_activity(
            apply_transform_rules,
            transform_input,
            task_queue=TRANSFORM_ENGINE_QUEUE,
            start_to_close_timeout=timedelta(minutes=5),
        )

        if not transform_output["success"]:
            return TransformPointer(
                success=False,
                message=transform_output.get("message", "Transform failed"),
                pipeline_run_id=pipeline_run_id,
                source_type=request.source_type,
                records_in=records_in,
            )

        transformed_records = transform_output["records"]
        rules_applied = transform_output.get("rules_applied", 0)
        records_out = len(transformed_records)

        # Step 5: Close pipeline run with results
        await workflow.execute_activity(
            close_pipeline_run,
            ClosePipelineRunRequest(
                pipeline_run_id=pipeline_run_id,
                status="completed",
                record_count=records_in,
                records_created=records_out,
            ),
            task_queue=DATA_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        return TransformPointer(
            success=True,
            message=f"Transformed {records_in} records → {records_out} via {rules_applied} rules",
            pipeline_run_id=pipeline_run_id,
            source_type=request.source_type,
            records_in=records_in,
            records_out=records_out,
            records_stored=records_out,
            rules_applied=rules_applied,
        )
