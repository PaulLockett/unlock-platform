"""Data Access activities.

Run on DATA_ACCESS_QUEUE. Called by IngestWorkflow to store transformed data,
and by QueryWorkflow to retrieve it.
"""

from temporalio import activity


@activity.defn
async def hello_store_data(transformed_data: str) -> str:
    """Placeholder: simulates storing transformed data."""
    activity.logger.info(f"Data Access: storing '{transformed_data[:50]}'")
    return f"Stored: {transformed_data}"
