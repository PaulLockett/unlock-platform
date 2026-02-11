"""ConfigureWorkflow: Validate inputs → Config Access.

Simplest workflow — takes validated configuration inputs and persists them
through Config Access.
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_config_access.activities import hello_load_config
    from unlock_shared.task_queues import CONFIG_ACCESS_QUEUE


@workflow.defn
class ConfigureWorkflow:
    """Persists pipeline configuration through Config Access."""

    @workflow.run
    async def run(self, config_key: str) -> str:
        result = await workflow.execute_activity(
            hello_load_config,
            config_key,
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )
        return f"Configuration saved: {result}"
