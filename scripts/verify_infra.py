"""Infrastructure verification script.

Starts multiple Temporal workers (one per component involved in IngestWorkflow),
executes the workflow, and verifies that activities dispatch across queues.

Prerequisites:
  - Temporal dev server running: `temporal server start-dev`
  - Dependencies installed: `uv sync`

Usage:
  uv run --package unlock-workers python scripts/verify_infra.py
"""

import asyncio
import logging
import uuid

from temporalio.worker import Worker

from unlock_shared.temporal_client import connect
from unlock_shared.task_queues import (
    DATA_ACCESS_QUEUE,
    DATA_MANAGER_QUEUE,
    SOURCE_ACCESS_QUEUE,
    TRANSFORM_ENGINE_QUEUE,
)
from unlock_data_manager.workflows.ingest import IngestWorkflow
from unlock_source_access.activities import hello_source_access
from unlock_transform_engine.activities import hello_transform
from unlock_data_access.activities import hello_store_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Run the full verification: start workers, execute workflow, check result."""
    client = await connect()
    logger.info("Connected to Temporal server")

    # Start four workers — one for the workflow runner, three for activities.
    # In production these are separate Railway services; here we run them
    # as concurrent tasks in one process to verify the dispatch pattern.
    async with (
        Worker(
            client,
            task_queue=DATA_MANAGER_QUEUE,
            workflows=[IngestWorkflow],
        ),
        Worker(
            client,
            task_queue=SOURCE_ACCESS_QUEUE,
            activities=[hello_source_access],
        ),
        Worker(
            client,
            task_queue=TRANSFORM_ENGINE_QUEUE,
            activities=[hello_transform],
        ),
        Worker(
            client,
            task_queue=DATA_ACCESS_QUEUE,
            activities=[hello_store_data],
        ),
    ):
        logger.info("All 4 workers started — dispatching IngestWorkflow")

        # Execute the workflow and wait for the result
        workflow_id = f"verify-infra-{uuid.uuid4()}"
        result = await client.execute_workflow(
            IngestWorkflow.run,
            "alabama-census-2024",
            id=workflow_id,
            task_queue=DATA_MANAGER_QUEUE,
        )

        logger.info(f"Workflow result: {result}")

        # Verify the result contains evidence of all three activity dispatches
        assert "Source Access" in result, f"Source Access activity didn't run: {result}"
        assert "Transformed" in result, f"Transform Engine activity didn't run: {result}"
        assert "Stored" in result, f"Data Access activity didn't run: {result}"

        logger.info("VERIFICATION PASSED — all activities dispatched across queues")


if __name__ == "__main__":
    asyncio.run(main())
