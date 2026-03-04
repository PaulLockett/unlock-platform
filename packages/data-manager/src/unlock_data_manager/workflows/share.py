"""ShareWorkflow: verify granter permissions → grant access to recipient.

Two-step orchestration:
1. CheckAccessWorkflow (child workflow on Access Engine queue) — verify the
   granter has "write" or "admin" on the view. Fail fast if not.
2. grant_access (Config Access activity) — add the permission for the recipient.

The access check is a CHILD WORKFLOW, not an activity, because permission
evaluation is the Access Engine's business logic — the Manager orchestrates
but doesn't implement the decision.
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_access_engine.workflows import CheckAccessWorkflow
    from unlock_config_access.activities import grant_access
    from unlock_shared.access_models import CheckAccessRequest
    from unlock_shared.config_models import GrantAccessRequest
    from unlock_shared.manager_models import ShareRequest, ShareResult
    from unlock_shared.task_queues import ACCESS_ENGINE_QUEUE, CONFIG_ACCESS_QUEUE


@workflow.defn
class ShareWorkflow:
    """Verifies granter permissions then grants access to a recipient."""

    @workflow.run
    async def run(self, request: ShareRequest) -> ShareResult:
        # Step 1: Verify granter has write or admin permission
        access_result = await workflow.execute_child_workflow(
            CheckAccessWorkflow.run,
            CheckAccessRequest(
                share_token=request.share_token,
                principal_id=request.granter_id,
                required_permission="write",
            ),
            id=f"{workflow.info().workflow_id}-check-access",
            task_queue=ACCESS_ENGINE_QUEUE,
        )

        if not access_result.success or not access_result.allowed:
            return ShareResult(
                success=False,
                message=(
                    f"Granter '{request.granter_id}' lacks "
                    f"write/admin permission: {access_result.reason}"
                ),
            )

        # Step 2: Grant access to recipient
        grant_result = await workflow.execute_activity(
            grant_access,
            GrantAccessRequest(
                view_id=access_result.view_id,
                principal_id=request.recipient_id,
                principal_type=request.recipient_type,
                permission=request.permission,
                granted_by=request.granter_id,
            ),
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not grant_result.success:
            return ShareResult(
                success=False,
                message=f"Failed to grant access: {grant_result.message}",
            )

        return ShareResult(
            success=True,
            message=f"Granted '{request.permission}' to '{request.recipient_id}'",
            view_id=access_result.view_id,
            share_token=request.share_token,
            granted_permission=request.permission,
        )
