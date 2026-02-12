"""Worker runner entrypoint.

Usage:
  python -m unlock_workers.runner <component-name>
  COMPONENT=source-access python -m unlock_workers.runner

Each Railway service sets a COMPONENT environment variable to select which
component to run. CLI argument takes precedence over COMPONENT env var.

This starts a Temporal worker that polls the component's dedicated task queue,
registering only that component's workflows and/or activities. The worker runs
until interrupted (SIGINT/SIGTERM), which Railway handles during deployments.
"""

import asyncio
import logging
import os
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

    # Temporal's Worker requires at least one activity or workflow.
    # Stub components (registered but not yet implemented) exit cleanly
    # instead of crash-looping on Railway.
    if not config.workflows and not config.activities:
        logger.info(
            f"Component '{component_name}' has no workflows or activities yet — "
            f"stub registered on queue '{config.task_queue}'. Exiting cleanly."
        )
        return

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
    """CLI entrypoint — parse the component name and start the worker.

    Precedence: CLI argument > COMPONENT env var.
    """
    component_name = sys.argv[1] if len(sys.argv) >= 2 else os.environ.get("COMPONENT", "")

    if not component_name:
        print("Usage: python -m unlock_workers.runner <component>")
        print("  or: COMPONENT=<component> python -m unlock_workers.runner")
        print(f"Components: {', '.join(sorted(COMPONENTS.keys()))}")
        sys.exit(1)

    asyncio.run(run_worker(component_name))


if __name__ == "__main__":
    main()
