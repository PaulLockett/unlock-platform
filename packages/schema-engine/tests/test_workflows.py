"""Tests for Schema Engine workflow structure and registry integration.

Full workflow tests with Temporal's WorkflowEnvironment belong in INT_TEST.
Here we verify structure, models, and registry imports.
"""

from __future__ import annotations

from unlock_schema_engine.workflows import (
    GenerateMappingsWorkflow,
    ValidateSchemaWorkflow,
)
from unlock_shared.models import PlatformResult
from unlock_shared.schema_models import (
    DriftReport,
    GenerateMappingsPointer,
    GenerateMappingsRequest,
    ValidateSchemaPointer,
    ValidateSchemaRequest,
)


class TestWorkflowStructure:
    def test_generate_mappings_is_decorated(self):
        assert hasattr(
            GenerateMappingsWorkflow,
            "__temporal_workflow_definition",
        )

    def test_validate_schema_is_decorated(self):
        assert hasattr(
            ValidateSchemaWorkflow,
            "__temporal_workflow_definition",
        )

    def test_generate_mappings_run_exists(self):
        wf = GenerateMappingsWorkflow()
        assert hasattr(wf, "run")

    def test_validate_schema_run_exists(self):
        wf = ValidateSchemaWorkflow()
        assert hasattr(wf, "run")


class TestSchemaModels:
    def test_generate_request(self):
        req = GenerateMappingsRequest(
            source_type="unipile",
            source_config={"auth_env_var": "KEY"},
        )
        assert req.source_type == "unipile"
        assert req.target_schema_id is None

    def test_generate_pointer_defaults(self):
        ptr = GenerateMappingsPointer(success=True, message="ok")
        assert ptr.schema_id == ""
        assert ptr.version == 0
        assert ptr.mappings_generated == 0
        assert ptr.unmapped_source_fields == []
        assert isinstance(ptr, PlatformResult)

    def test_validate_request(self):
        req = ValidateSchemaRequest(schema_id="s-001")
        assert req.schema_id == "s-001"
        assert req.source_type is None

    def test_validate_pointer_defaults(self):
        ptr = ValidateSchemaPointer(success=True, message="ok")
        assert ptr.is_valid is False
        assert ptr.drift_detected is False
        assert isinstance(ptr, PlatformResult)

    def test_drift_report_defaults(self):
        dr = DriftReport()
        assert dr.has_drift is False
        assert dr.new_fields == []
        assert dr.missing_fields == []
        assert dr.type_changes == []

    def test_registry_imports_schema_engine(self):
        from unlock_workers.registry import COMPONENTS

        cfg = COMPONENTS["schema-engine"]
        assert cfg.task_queue == "schema-engine-queue"
        assert len(cfg.workflows) == 2
        assert len(cfg.activities) == 3
