"""Task queue name constants for each component.

Every component runs on its own Temporal worker with a dedicated task queue.
This gives us independent scaling, isolation, and deployment — critical because
Python's GIL means a single worker process running all activities becomes a
bottleneck under load.

These constants are the single source of truth for queue names. Both the worker
runner (which starts workers listening on the right queue) and the workflow
definitions (which dispatch activities to the right queue) reference these.
"""

# Manager — runs workflows that orchestrate activities across other queues
DATA_MANAGER_QUEUE = "data-manager-queue"

# Engines — business logic activities
TRANSFORM_ENGINE_QUEUE = "transform-engine-queue"
SCHEMA_ENGINE_QUEUE = "schema-engine-queue"
ACCESS_ENGINE_QUEUE = "access-engine-queue"

# Resource Access — storage abstraction activities
SOURCE_ACCESS_QUEUE = "source-access-queue"
DATA_ACCESS_QUEUE = "data-access-queue"
CONFIG_ACCESS_QUEUE = "config-access-queue"

# Utilities
LLM_GATEWAY_QUEUE = "llm-gateway-queue"
SCHEDULER_QUEUE = "scheduler-queue"
