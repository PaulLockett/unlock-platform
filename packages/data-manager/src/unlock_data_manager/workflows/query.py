"""QueryWorkflow: Config Access → Data Access → Schema Engine → Access Engine.

Handles data queries by:
1. Loading the relevant configuration (what data, what schema)
2. Fetching the data
3. Validating the schema
4. Checking access permissions
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_access_engine.activities import hello_check_access
    from unlock_config_access.activities import hello_load_config
    from unlock_data_access.activities import hello_store_data
    from unlock_schema_engine.activities import hello_validate_schema
    from unlock_shared.task_queues import (
        ACCESS_ENGINE_QUEUE,
        CONFIG_ACCESS_QUEUE,
        DATA_ACCESS_QUEUE,
        SCHEMA_ENGINE_QUEUE,
    )


@workflow.defn
class QueryWorkflow:
    """Orchestrates a data query across four worker queues."""

    @workflow.run
    async def run(self, query_key: str, user_id: str) -> str:
        config = await workflow.execute_activity(
            hello_load_config,
            query_key,
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        data = await workflow.execute_activity(
            hello_store_data,
            config,
            task_queue=DATA_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        validated = await workflow.execute_activity(
            hello_validate_schema,
            data,
            task_queue=SCHEMA_ENGINE_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        access_result = await workflow.execute_activity(
            hello_check_access,
            user_id,
            task_queue=ACCESS_ENGINE_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        return f"Query result: {validated} | {access_result}"
