"""ShareWorkflow: Config Access → Access Engine → generate link.

Creates a shareable data view by:
1. Loading the configuration for what data to share
2. Checking/granting access permissions
3. Generating a share link
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_access_engine.activities import hello_check_access
    from unlock_config_access.activities import hello_load_config
    from unlock_shared.task_queues import ACCESS_ENGINE_QUEUE, CONFIG_ACCESS_QUEUE


@workflow.defn
class ShareWorkflow:
    """Creates a shareable link to a data view."""

    @workflow.run
    async def run(self, config_key: str, user_id: str) -> str:
        config = await workflow.execute_activity(
            hello_load_config,
            config_key,
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        access = await workflow.execute_activity(
            hello_check_access,
            user_id,
            task_queue=ACCESS_ENGINE_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        return f"Share link generated: {config} | {access}"
