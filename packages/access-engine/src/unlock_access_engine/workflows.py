"""Access Control Engine workflows: child workflows dispatched by Data Manager.

Encapsulates the volatility of WHO can access WHAT data under WHAT conditions.
Permission models evolve independently from data and transformation logic.

Two workflows:
  CheckAccessWorkflow         — binary access decision for a specific request
  EvaluatePermissionsWorkflow — aggregate effective permissions for a principal
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_config_access.activities import retrieve_view
    from unlock_shared.access_models import (
        CheckAccessPointer,
        CheckAccessRequest,
        EvaluatePermissionsPointer,
        EvaluatePermissionsRequest,
    )
    from unlock_shared.config_models import RetrieveViewRequest
    from unlock_shared.task_queues import (
        ACCESS_ENGINE_QUEUE,
        CONFIG_ACCESS_QUEUE,
    )

    from unlock_access_engine.activities import (
        compute_effective_permissions,
        evaluate_access_decision,
    )


@workflow.defn
class CheckAccessWorkflow:
    """Fetch view + permissions, evaluate access, return decision."""

    @workflow.run
    async def run(
        self, request: CheckAccessRequest,
    ) -> CheckAccessPointer:
        # Step 1: Get view + permissions from Config Access
        view_result = await workflow.execute_activity(
            retrieve_view,
            RetrieveViewRequest(share_token=request.share_token),
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not view_result.success:
            return CheckAccessPointer(
                success=False,
                message=(
                    f"Failed to retrieve view: {view_result.message}"
                ),
                allowed=False,
                reason="view_not_found",
            )

        # Step 2: Evaluate access (engine activity — pure logic)
        decision_input = {
            "permissions": view_result.permissions,
            "principal_id": request.principal_id,
            "principal_type": request.principal_type,
            "required_permission": request.required_permission,
            "view": view_result.view,
        }
        decision = await workflow.execute_activity(
            evaluate_access_decision,
            decision_input,
            task_queue=ACCESS_ENGINE_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        view_id = ""
        if view_result.view:
            view_id = view_result.view.get("id", "")

        return CheckAccessPointer(
            success=True,
            message=decision.get("reason", ""),
            allowed=decision.get("allowed", False),
            view_id=view_id,
            matched_permission=decision.get(
                "matched_permission", "",
            ),
            reason=decision.get("reason", ""),
        )


@workflow.defn
class EvaluatePermissionsWorkflow:
    """Fetch view + permissions, compute effective permissions for principal."""

    @workflow.run
    async def run(
        self, request: EvaluatePermissionsRequest,
    ) -> EvaluatePermissionsPointer:
        # Step 1: Get view + permissions from Config Access
        view_result = await workflow.execute_activity(
            retrieve_view,
            RetrieveViewRequest(share_token=request.share_token),
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not view_result.success:
            return EvaluatePermissionsPointer(
                success=False,
                message=(
                    f"Failed to retrieve view: {view_result.message}"
                ),
            )

        # Step 2: Compute effective permissions (engine activity)
        perms_input = {
            "permissions": view_result.permissions,
            "principal_id": request.principal_id,
            "principal_type": request.principal_type,
            "resource_type": request.resource_type,
        }
        effective = await workflow.execute_activity(
            compute_effective_permissions,
            perms_input,
            task_queue=ACCESS_ENGINE_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        return EvaluatePermissionsPointer(
            success=True,
            message=(
                f"Found {effective.get('total_count', 0)} "
                f"permissions for {request.principal_id}"
            ),
            view_ids=effective.get("view_ids", []),
            permission_levels=effective.get("permission_levels", {}),
            total_count=effective.get("total_count", 0),
        )
