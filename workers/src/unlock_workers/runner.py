"""Worker runner entrypoint.

Usage: python -m unlock_workers.runner <component-name>

Each Railway service runs the same Docker image with a different CMD argument:
  CMD ["python", "-m", "unlock_workers.runner", "source-access"]
  CMD ["python", "-m", "unlock_workers.runner", "data-manager"]
  etc.

This starts a Temporal worker that polls the component's dedicated task queue,
registering only that component's workflows and/or activities. The worker runs
until interrupted (SIGINT/SIGTERM), which Railway handles during deployments.
"""

import asyncio
import logging
import sys

from temporalio.worker import Worker
from unlock_shared.temporal_client import connect

from unlock_workers.registry import COMPONENTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_worker(component_name: str) -> None:
    """Start a Temporal worker for the specified component."""
    if component_name not in COMPONENTS:
        available = ", ".join(sorted(COMPONENTS.keys()))
        logger.error(f"Unknown component '{component_name}'. Available: {available}")
        sys.exit(1)

    config = COMPONENTS[component_name]
    client = await connect()

    logger.info(
        f"Starting worker for '{component_name}' on queue '{config.task_queue}' "
        f"(workflows={len(config.workflows)}, activities={len(config.activities)})"
    )

    worker = Worker(
        client,
        task_queue=config.task_queue,
        workflows=config.workflows,
        activities=config.activities,
    )

    await worker.run()


def main() -> None:
    """CLI entrypoint — parse the component name and start the worker."""
    if len(sys.argv) != 2:
        print("Usage: python -m unlock_workers.runner <component>")
        print(f"Components: {', '.join(sorted(COMPONENTS.keys()))}")
        sys.exit(1)

    component_name = sys.argv[1]
    asyncio.run(run_worker(component_name))


if __name__ == "__main__":
    main()
