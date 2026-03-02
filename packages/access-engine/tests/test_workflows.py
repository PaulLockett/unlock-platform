"""Tests for Access Engine workflows — structural verification.

Workflow integration tests (multi-queue activity dispatch) belong in
INT_TEST. Here we verify: correct Temporal decorators, model defaults,
and registry import integrity.
"""

from __future__ import annotations

from temporalio import workflow
from unlock_access_engine.workflows import (
    CheckAccessWorkflow,
    EvaluatePermissionsWorkflow,
)
from unlock_shared.access_models import (
    CheckAccessPointer,
    CheckAccessRequest,
    EvaluatePermissionsPointer,
    EvaluatePermissionsRequest,
)

# ============================================================================
# Workflow decoration
# ============================================================================


class TestWorkflowStructure:
    """Verify workflows are properly decorated for Temporal."""

    def test_check_access_is_workflow(self):
        defn = workflow._Definition.from_class(CheckAccessWorkflow)
        assert defn is not None

    def test_evaluate_permissions_is_workflow(self):
        defn = workflow._Definition.from_class(EvaluatePermissionsWorkflow)
        assert defn is not None

    def test_check_access_has_run_method(self):
        assert hasattr(CheckAccessWorkflow, "run")

    def test_evaluate_permissions_has_run_method(self):
        assert hasattr(EvaluatePermissionsWorkflow, "run")


# ============================================================================
# Model defaults
# ============================================================================


class TestModelDefaults:
    """Verify boundary model defaults match the plan."""

    def test_check_access_request_defaults(self):
        req = CheckAccessRequest(
            share_token="tok-abc",
            principal_id="user-1",
        )
        assert req.principal_type == "user"
        assert req.required_permission == "read"

    def test_check_access_pointer_defaults(self):
        ptr = CheckAccessPointer(success=True, message="ok")
        assert ptr.allowed is False
        assert ptr.view_id == ""
        assert ptr.matched_permission == ""
        assert ptr.reason == ""

    def test_evaluate_permissions_request_defaults(self):
        req = EvaluatePermissionsRequest(
            share_token="tok-abc",
            principal_id="user-1",
        )
        assert req.principal_type == "user"
        assert req.resource_type is None

    def test_evaluate_permissions_pointer_defaults(self):
        ptr = EvaluatePermissionsPointer(success=True, message="ok")
        assert ptr.view_ids == []
        assert ptr.permission_levels == {}
        assert ptr.total_count == 0


# ============================================================================
# Registry import
# ============================================================================


class TestRegistryImport:
    """Verify the registry can import all access engine components."""

    def test_import_activities(self):
        from unlock_access_engine.activities import (
            compute_effective_permissions,
            evaluate_access_decision,
            hello_check_access,
        )

        assert callable(hello_check_access)
        assert callable(evaluate_access_decision)
        assert callable(compute_effective_permissions)

    def test_import_workflows(self):
        from unlock_access_engine.workflows import (
            CheckAccessWorkflow,
            EvaluatePermissionsWorkflow,
        )

        assert CheckAccessWorkflow is not None
        assert EvaluatePermissionsWorkflow is not None
