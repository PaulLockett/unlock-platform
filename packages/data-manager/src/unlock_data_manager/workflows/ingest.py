"""IngestWorkflow: Source Access → Data Access → Transform Engine.

The primary data ingestion pipeline orchestrating three components:
1. Open pipeline run (Data Access) — start tracking the ingestion
2. Harvest records (Source Access) — fetch raw data from external source
3. Catalog content (Data Access) — store raw records as ContentRecords
4. TransformWorkflow (child workflow on Transform Engine queue) — apply pipeline
5. Close pipeline run (Data Access) — record final metrics

The Transform Engine is dispatched as a CHILD WORKFLOW, not an activity,
because transformation is the engine's business logic. The Manager tracks the
ingest-level pipeline run; the TransformWorkflow manages its own internal run.

FetchResult.records (list[dict]) are mapped to ContentRecord with best-effort
field mapping via .get() — missing fields get None/defaults.
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_config_access.activities import cache_source_records
    from unlock_data_access.activities import (
        catalog_content,
        close_pipeline_run,
        open_pipeline_run,
    )
    from unlock_shared.data_models import (
        CatalogContentRequest,
        ClosePipelineRunRequest,
        ContentRecord,
        OpenPipelineRunRequest,
    )
    from unlock_shared.manager_models import IngestRequest, IngestResult
    from unlock_shared.source_models import FetchRequest
    from unlock_shared.task_queues import (
        CONFIG_ACCESS_QUEUE,
        DATA_ACCESS_QUEUE,
        SOURCE_ACCESS_QUEUE,
        TRANSFORM_ENGINE_QUEUE,
    )
    from unlock_shared.transform_models import TransformRequest
    from unlock_source_access.activities import harvest_records
    from unlock_transform_engine.workflows import TransformWorkflow


@workflow.defn
class IngestWorkflow:
    """Orchestrates the full ingestion pipeline across three worker queues."""

    @workflow.run
    async def run(self, request: IngestRequest) -> IngestResult:
        # Step 1: Open pipeline run for tracking
        run_result = await workflow.execute_activity(
            open_pipeline_run,
            OpenPipelineRunRequest(
                source_key=request.source_name,
                workflow_run_id=workflow.info().workflow_id,
                resource_type=request.resource_type,
            ),
            task_queue=DATA_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not run_result.success:
            return IngestResult(
                success=False,
                message=f"Failed to open pipeline run: {run_result.message}",
                source_name=request.source_name,
            )

        pipeline_run_id = run_result.pipeline_run_id

        # Step 2: Harvest records from Source Access
        fetch_result = await workflow.execute_activity(
            harvest_records,
            FetchRequest(
                source_id=request.source_name,
                source_type=request.source_type,
                resource_type=request.resource_type,
                since=request.since,
                max_pages=request.max_pages,
                auth_env_var=request.auth_env_var,
                base_url=request.base_url,
                config_json=request.config_json,
            ),
            task_queue=SOURCE_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(minutes=5),
            heartbeat_timeout=timedelta(seconds=60),
        )

        if not fetch_result.success:
            await self._close_run(pipeline_run_id, "failed", 0, error=fetch_result.message)
            return IngestResult(
                success=False,
                message=f"Harvest failed: {fetch_result.message}",
                source_name=request.source_name,
                pipeline_run_id=pipeline_run_id,
            )

        records_fetched = fetch_result.record_count

        if records_fetched == 0:
            await self._close_run(pipeline_run_id, "completed", 0)
            return IngestResult(
                success=True,
                message="No records to ingest",
                source_name=request.source_name,
                pipeline_run_id=pipeline_run_id,
                records_fetched=0,
            )

        # Step 2b: Cache raw records in Redis for fast Canvas query reads
        await workflow.execute_activity(
            cache_source_records,
            {
                "source_key": request.source_name,
                "records": fetch_result.records,
            },
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 3: Catalog raw records as ContentRecords in Data Access
        channel_key = request.channel_key or request.source_type
        content_records = [
            ContentRecord(
                channel_key=channel_key,
                content_type=r.get("content_type", request.resource_type),
                source_key=request.source_name,
                pipeline_run_id=pipeline_run_id,
                external_id=r.get("external_id") or r.get("id"),
                title=r.get("title"),
                body=r.get("body") or r.get("text") or r.get("content"),
                url=r.get("url"),
                published_at=None,
                like_count=r.get("like_count", 0),
                comment_count=r.get("comment_count", 0),
                share_count=r.get("share_count", 0),
                view_count=r.get("view_count", 0),
            )
            for r in fetch_result.records
        ]

        catalog_result = await workflow.execute_activity(
            catalog_content,
            CatalogContentRequest(
                records=content_records,
                source_key=request.source_name,
            ),
            task_queue=DATA_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(minutes=2),
        )

        if not catalog_result.success:
            await self._close_run(
                pipeline_run_id, "failed", records_fetched,
                error=catalog_result.message,
            )
            return IngestResult(
                success=False,
                message=f"Catalog failed: {catalog_result.message}",
                source_name=request.source_name,
                pipeline_run_id=pipeline_run_id,
                records_fetched=records_fetched,
            )

        records_stored = catalog_result.created + catalog_result.updated

        # Step 4: Dispatch TransformWorkflow as child workflow
        transform_result = await workflow.execute_child_workflow(
            TransformWorkflow.run,
            TransformRequest(
                source_type=request.source_type,
                pipeline_run_id=pipeline_run_id,
            ),
            id=f"{workflow.info().workflow_id}-transform",
            task_queue=TRANSFORM_ENGINE_QUEUE,
        )

        records_transformed = transform_result.records_out if transform_result.success else 0

        # Step 5: Close pipeline run
        await self._close_run(
            pipeline_run_id,
            "completed",
            records_fetched,
            records_created=records_stored,
        )

        return IngestResult(
            success=True,
            message=(
                f"Ingested {records_fetched} records from '{request.source_name}': "
                f"{records_stored} stored, {records_transformed} transformed"
            ),
            source_name=request.source_name,
            pipeline_run_id=pipeline_run_id,
            records_fetched=records_fetched,
            records_stored=records_stored,
            records_transformed=records_transformed,
        )

    async def _close_run(
        self,
        pipeline_run_id: str,
        status: str,
        record_count: int,
        *,
        records_created: int = 0,
        error: str | None = None,
    ) -> None:
        """Close the pipeline run — best-effort, doesn't block on failure."""
        await workflow.execute_activity(
            close_pipeline_run,
            ClosePipelineRunRequest(
                pipeline_run_id=pipeline_run_id,
                status=status,
                record_count=record_count,
                records_created=records_created,
                error_message=error,
            ),
            task_queue=DATA_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )
