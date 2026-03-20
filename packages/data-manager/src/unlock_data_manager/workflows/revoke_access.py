"""RevokeAccessWorkflow: remove a permission grant on a view.

Single-step dispatch to the revoke_access activity on Config Access.
Cascades revocation to cloned child views.
Used by /api/share/revoke (admin only).
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_config_access.activities import revoke_access
    from unlock_shared.config_models import RevokeAccessRequest, RevokeAccessResult
    from unlock_shared.task_queues import CONFIG_ACCESS_QUEUE


@workflow.defn
class RevokeAccessWorkflow:
    """Revoke access on a view for a specific principal."""

    @workflow.run
    async def run(self, request: RevokeAccessRequest) -> RevokeAccessResult:
        return await workflow.execute_activity(
            revoke_access,
            request,
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )
