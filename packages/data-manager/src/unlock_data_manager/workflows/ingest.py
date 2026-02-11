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
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_data_access.activities import hello_store_data
    from unlock_shared.task_queues import (
        DATA_ACCESS_QUEUE,
        SOURCE_ACCESS_QUEUE,
        TRANSFORM_ENGINE_QUEUE,
    )
    from unlock_source_access.activities import hello_source_access
    from unlock_transform_engine.activities import hello_transform


@workflow.defn
class IngestWorkflow:
    """Orchestrates the full ingestion pipeline across three worker queues."""

    @workflow.run
    async def run(self, source_name: str) -> str:
        # Step 1: Fetch raw data from the source
        raw_data = await workflow.execute_activity(
            hello_source_access,
            source_name,
            task_queue=SOURCE_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 2: Transform the raw data
        transformed = await workflow.execute_activity(
            hello_transform,
            raw_data,
            task_queue=TRANSFORM_ENGINE_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Step 3: Store the result
        stored = await workflow.execute_activity(
            hello_store_data,
            transformed,
            task_queue=DATA_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        return stored
