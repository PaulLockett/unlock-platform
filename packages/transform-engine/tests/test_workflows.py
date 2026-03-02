"""Tests for TransformWorkflow structure and registry integration.

Full workflow tests with Temporal's WorkflowEnvironment require a running
test server with multiple workers. Those belong in INT_TEST. Here we verify:
  - Workflow class is properly decorated
  - Registry imports succeed (proves all activities/workflows are valid)
  - Workflow can be instantiated
"""

from __future__ import annotations

from unlock_shared.transform_models import TransformPointer, TransformRequest
from unlock_transform_engine.workflows import TransformWorkflow


class TestTransformWorkflowStructure:
    def test_workflow_is_decorated(self):
        """TransformWorkflow must have Temporal workflow definition."""
        assert hasattr(TransformWorkflow, "__temporal_workflow_definition")

    def test_workflow_run_method_exists(self):
        """The run method must exist and be the workflow entry point."""
        wf = TransformWorkflow()
        assert hasattr(wf, "run")

    def test_request_model_fields(self):
        req = TransformRequest(source_type="unipile")
        assert req.source_type == "unipile"
        assert req.pipeline_run_id is None

    def test_pointer_model_defaults(self):
        ptr = TransformPointer(success=True, message="ok")
        assert ptr.pipeline_run_id == ""
        assert ptr.records_in == 0
        assert ptr.records_out == 0
        assert ptr.records_stored == 0
        assert ptr.rules_applied == 0

    def test_pointer_extends_platform_result(self):
        from unlock_shared.models import PlatformResult

        ptr = TransformPointer(success=True, message="ok")
        assert isinstance(ptr, PlatformResult)

    def test_registry_imports_transform_engine(self):
        """Registry import proves workflow + activities are valid."""
        from unlock_workers.registry import COMPONENTS

        cfg = COMPONENTS["transform-engine"]
        assert cfg.task_queue == "transform-engine-queue"
        assert len(cfg.workflows) == 1
        assert len(cfg.activities) == 3
