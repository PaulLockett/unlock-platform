"""Config Access activities.

Run on CONFIG_ACCESS_QUEUE. Called by ConfigureWorkflow and QueryWorkflow
to manage pipeline and schema configurations.
"""

from temporalio import activity


@activity.defn
async def hello_load_config(config_key: str) -> str:
    """Placeholder: simulates loading a pipeline configuration."""
    activity.logger.info(f"Config Access: loading config '{config_key}'")
    return f"Config loaded: {config_key}"
