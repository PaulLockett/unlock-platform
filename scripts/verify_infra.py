"""Infrastructure verification script.

Starts multiple Temporal workers (one per component involved in IngestWorkflow),
executes the workflow, and verifies that activities dispatch across queues.

The Source Access worker now registers the four real activities (connect_source,
fetch_source_data, test_connection, get_source_schema) instead of the hello-world
stub. The workflow will call fetch_source_data, which will fail gracefully if
UNIPILE_API_KEY isn't set — we verify the dispatch pattern works regardless.

Prerequisites:
  - Temporal dev server running: `temporal server start-dev`
    OR Temporal Cloud credentials in .env
  - Dependencies installed: `uv sync`

Usage:
  uv run --package unlock-workers python scripts/verify_infra.py
"""

import asyncio
import logging
import uuid

from temporalio.worker import Worker
from unlock_data_access.activities import hello_store_data
from unlock_data_manager.workflows.ingest import IngestWorkflow
from unlock_shared.task_queues import (
    DATA_ACCESS_QUEUE,
    DATA_MANAGER_QUEUE,
    SOURCE_ACCESS_QUEUE,
    TRANSFORM_ENGINE_QUEUE,
)
from unlock_shared.temporal_client import connect
from unlock_source_access.activities import (
    connect_source,
    fetch_source_data,
    get_source_schema,
    test_connection,
)
from unlock_transform_engine.activities import hello_transform

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
            activities=[connect_source, fetch_source_data, test_connection, get_source_schema],
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

        workflow_id = f"verify-infra-{uuid.uuid4()}"
        result = await client.execute_workflow(
            IngestWorkflow.run,
            "alabama-census-2024",
            id=workflow_id,
            task_queue=DATA_MANAGER_QUEUE,
        )

        logger.info(f"Workflow result: {result}")

        # The workflow now returns a string from the downstream stubs.
        # Source Access will fail gracefully (no UNIPILE_API_KEY) but the
        # dispatch pattern still works — the activity executes on the
        # source-access queue and returns a FetchResult with success=False.
        assert "Source Access" in result, f"Source Access activity didn't run: {result}"
        assert "Transformed" in result, f"Transform Engine activity didn't run: {result}"
        assert "Stored" in result, f"Data Access activity didn't run: {result}"

        logger.info("VERIFICATION PASSED — all activities dispatched across queues")


if __name__ == "__main__":
    asyncio.run(main())
