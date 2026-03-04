"""Infrastructure verification script.

Starts multiple Temporal workers (one per component involved in IngestWorkflow),
executes the workflow, and verifies that activities dispatch across queues.

The IngestWorkflow now uses typed IngestRequest and dispatches real activities
plus a child TransformWorkflow. Workers register the full activity sets needed
for the complete pipeline.

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
from unlock_config_access.activities import (
    survey_configs,
)
from unlock_data_access.activities import (
    catalog_content,
    close_pipeline_run,
    open_pipeline_run,
    survey_engagement,
)
from unlock_data_manager.workflows.ingest import IngestWorkflow
from unlock_shared.manager_models import IngestRequest
from unlock_shared.task_queues import (
    CONFIG_ACCESS_QUEUE,
    DATA_ACCESS_QUEUE,
    DATA_MANAGER_QUEUE,
    SOURCE_ACCESS_QUEUE,
    TRANSFORM_ENGINE_QUEUE,
)
from unlock_shared.temporal_client import connect
from unlock_source_access.activities import (
    harvest_records,
)
from unlock_transform_engine.activities import apply_transform_rules
from unlock_transform_engine.workflows import TransformWorkflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Run the full verification: start workers, execute workflow, check result."""
    client = await connect()
    logger.info("Connected to Temporal server")

    # Start five workers — one for the workflow runner, four for activities.
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
            activities=[harvest_records],
        ),
        Worker(
            client,
            task_queue=TRANSFORM_ENGINE_QUEUE,
            workflows=[TransformWorkflow],
            activities=[apply_transform_rules],
        ),
        Worker(
            client,
            task_queue=DATA_ACCESS_QUEUE,
            activities=[
                open_pipeline_run,
                catalog_content,
                close_pipeline_run,
                survey_engagement,
            ],
        ),
        Worker(
            client,
            task_queue=CONFIG_ACCESS_QUEUE,
            activities=[survey_configs],
        ),
    ):
        logger.info("All 5 workers started — dispatching IngestWorkflow")

        workflow_id = f"verify-infra-{uuid.uuid4()}"
        request = IngestRequest(
            source_name="alabama-census-2024",
            source_type="unipile",
            resource_type="posts",
            auth_env_var="UNIPILE_API_KEY",
        )

        result = await client.execute_workflow(
            IngestWorkflow.run,
            request,
            id=workflow_id,
            task_queue=DATA_MANAGER_QUEUE,
        )

        logger.info(f"Workflow result: success={result.success}, message={result.message}")

        # The workflow returns an IngestResult. Verify the pipeline ran.
        assert isinstance(result.source_name, str), f"Expected source_name string: {result}"
        assert result.pipeline_run_id != "", f"Expected pipeline_run_id: {result}"

        logger.info("VERIFICATION PASSED — IngestWorkflow dispatched across queues")


if __name__ == "__main__":
    asyncio.run(main())
