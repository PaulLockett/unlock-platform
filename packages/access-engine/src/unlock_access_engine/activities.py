"""Access Control Engine activities.

Run on ACCESS_ENGINE_QUEUE. Called by QueryWorkflow and ShareWorkflow
to enforce role-based permissions.
"""

from temporalio import activity


@activity.defn
async def hello_check_access(user_id: str) -> str:
    """Placeholder: simulates checking user access permissions."""
    activity.logger.info(f"Access Engine: checking access for user '{user_id}'")
    return f"Access granted: {user_id}"
