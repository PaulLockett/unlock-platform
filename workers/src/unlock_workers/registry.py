"""Component registry: maps component names to their workflows and activities.

This is the central lookup table that the runner uses to determine what to
register on a worker based on the CLI argument. Each component entry specifies:

- task_queue: Which Temporal task queue this worker polls
- workflows: Workflow classes to register (only the Data Manager has these)
- activities: Activity functions to register

The key insight: every Railway service uses the same Docker image. The only
difference is the CMD argument (e.g., "source-access"), which selects which
entry from this registry to use. This keeps the build simple (one Dockerfile)
while maintaining complete runtime isolation between components.
"""

from dataclasses import dataclass, field
from typing import Any

from unlock_access_engine.activities import hello_check_access
from unlock_config_access.activities import hello_load_config
from unlock_data_access.activities import hello_store_data
from unlock_data_manager.workflows.configure import ConfigureWorkflow
from unlock_data_manager.workflows.ingest import IngestWorkflow
from unlock_data_manager.workflows.query import QueryWorkflow
from unlock_data_manager.workflows.share import ShareWorkflow
from unlock_llm_gateway.activities import hello_llm_assess
from unlock_schema_engine.activities import hello_validate_schema
from unlock_shared.task_queues import (
    ACCESS_ENGINE_QUEUE,
    CONFIG_ACCESS_QUEUE,
    DATA_ACCESS_QUEUE,
    DATA_MANAGER_QUEUE,
    LLM_GATEWAY_QUEUE,
    SCHEMA_ENGINE_QUEUE,
    SOURCE_ACCESS_QUEUE,
    TRANSFORM_ENGINE_QUEUE,
)
from unlock_source_access.activities import (
    connect_source,
    fetch_source_data,
    get_source_schema,
    test_connection,
)
from unlock_transform_engine.activities import hello_transform


@dataclass
class ComponentConfig:
    """Configuration for a single component's worker."""

    task_queue: str
    workflows: list[Any] = field(default_factory=list)
    activities: list[Any] = field(default_factory=list)


COMPONENTS: dict[str, ComponentConfig] = {
    "data-manager": ComponentConfig(
        task_queue=DATA_MANAGER_QUEUE,
        workflows=[IngestWorkflow, QueryWorkflow, ConfigureWorkflow, ShareWorkflow],
    ),
    "source-access": ComponentConfig(
        task_queue=SOURCE_ACCESS_QUEUE,
        activities=[connect_source, fetch_source_data, test_connection, get_source_schema],
    ),
    "transform-engine": ComponentConfig(
        task_queue=TRANSFORM_ENGINE_QUEUE,
        activities=[hello_transform],
    ),
    "data-access": ComponentConfig(
        task_queue=DATA_ACCESS_QUEUE,
        activities=[hello_store_data],
    ),
    "config-access": ComponentConfig(
        task_queue=CONFIG_ACCESS_QUEUE,
        activities=[hello_load_config],
    ),
    "schema-engine": ComponentConfig(
        task_queue=SCHEMA_ENGINE_QUEUE,
        activities=[hello_validate_schema],
    ),
    "access-engine": ComponentConfig(
        task_queue=ACCESS_ENGINE_QUEUE,
        activities=[hello_check_access],
    ),
    "llm-gateway": ComponentConfig(
        task_queue=LLM_GATEWAY_QUEUE,
        activities=[hello_llm_assess],
    ),
}
