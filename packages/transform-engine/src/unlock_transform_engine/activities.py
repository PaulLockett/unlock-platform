"""Transformation Engine activities.

Run on TRANSFORM_ENGINE_QUEUE. Called by IngestWorkflow after Source Access
fetches raw data — applies configurable transformation pipelines.
"""

from temporalio import activity


@activity.defn
async def hello_transform(raw_data: str) -> str:
    """Placeholder: simulates transforming raw data through a pipeline."""
    activity.logger.info(f"Transform Engine: transforming '{raw_data[:50]}'")
    return f"Transformed: {raw_data}"
