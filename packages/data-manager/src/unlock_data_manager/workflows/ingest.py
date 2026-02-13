"""IngestWorkflow: Source Access → Transform Engine → Data Access.

This is the primary data ingestion pipeline. It orchestrates three separate
components, each running on its own worker:

1. Source Access (source-access-queue): Fetch raw data from an external source
2. Transform Engine (transform-engine-queue): Apply transformation pipeline
3. Data Access (data-access-queue): Store the transformed result

The workflow itself runs on data-manager-queue, but each activity is dispatched
to the specific component's queue via `task_queue=`. This means the activity
executes on whatever worker is listening on that queue — a completely separate
process, potentially on a different machine.

Source Access now uses typed models (FetchRequest → FetchResult) instead of
plain strings. Transform and Data Access are still hello-world stubs — they'll
be upgraded in their respective tasks.
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_data_access.activities import hello_store_data
    from unlock_shared.source_models import FetchRequest, FetchResult
    from unlock_shared.task_queues import (
        DATA_ACCESS_QUEUE,
        SOURCE_ACCESS_QUEUE,
        TRANSFORM_ENGINE_QUEUE,
    )
    from unlock_source_access.activities import fetch_source_data
    from unlock_transform_engine.activities import hello_transform


@workflow.defn
class IngestWorkflow:
    """Orchestrates the full ingestion pipeline across three worker queues."""

    @workflow.run
    async def run(self, source_name: str) -> str:
        # Step 1: Fetch raw data from the source using typed models.
        # Build a FetchRequest from the source_name — downstream tasks will
        # pass richer configs, but for now we support the simple string interface
        # for backward compatibility with verify_infra.py.
        request = FetchRequest(
            source_id=source_name,
            source_type="unipile",
            resource_type="posts",
            auth_env_var="UNIPILE_API_KEY",
        )
        fetch_result: FetchResult = await workflow.execute_activity(
            fetch_source_data,
            request,
            task_queue=SOURCE_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(minutes=5),
            heartbeat_timeout=timedelta(seconds=60),
        )

        # Pass a summary string to downstream stubs (they still expect strings).
        # When Transform Engine is implemented, this will pass FetchResult directly.
        raw_summary = (
            f"Source Access fetched {fetch_result.record_count} records "
            f"from '{source_name}' (success={fetch_result.success})"
        )

        # Step 2: Transform the raw data (still hello-world stub)
        transformed = await workflow.execute_activity(
            hello_transform,
            raw_summary,
            task_queue=TRANSFORM_ENGINE_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 3: Store the result (still hello-world stub)
        stored = await workflow.execute_activity(
            hello_store_data,
            transformed,
            task_queue=DATA_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        return stored
