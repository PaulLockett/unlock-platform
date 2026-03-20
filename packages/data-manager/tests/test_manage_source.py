"""Tests for ManageSourceWorkflow — structural verification.

Follows the same pattern as test_workflows.py: verify decoration,
model contracts, and registry integration. Behavioral tests belong in INT_TEST.
"""

from __future__ import annotations

import json

from unlock_data_manager.workflows.manage_source import ManageSourceWorkflow
from unlock_shared.source_models import (
    IdentifySourceRequest,
    IdentifySourceResult,
    RegisterSourceRequest,
    RegisterSourceResult,
)


class TestManageSourceWorkflowStructure:
    def test_is_decorated(self):
        assert hasattr(ManageSourceWorkflow, "__temporal_workflow_definition")

    def test_has_run(self):
        assert hasattr(ManageSourceWorkflow(), "run")


class TestManageSourceModels:
    def test_identify_request_defaults(self):
        req = IdentifySourceRequest()
        assert req.name is None
        assert req.source_type is None

    def test_identify_result_defaults(self):
        r = IdentifySourceResult(success=True, message="ok")
        assert r.exact_match is None
        assert r.possible_matches == []
        assert r.all_sources is None

    def test_register_request_required(self):
        req = RegisterSourceRequest(name="test", protocol="rest_api")
        assert req.service == ""
        assert req.resource_type == "posts"

    def test_register_result_defaults(self):
        r = RegisterSourceResult(success=True, message="ok")
        assert r.source == {}


class TestManageSourceSerialization:
    def test_identify_request_roundtrip(self):
        req = IdentifySourceRequest(name="Meta Ads", source_type="file_upload")
        data = json.loads(req.model_dump_json())
        restored = IdentifySourceRequest(**data)
        assert restored.name == "Meta Ads"

    def test_identify_result_roundtrip(self):
        r = IdentifySourceResult(
            success=True,
            message="found",
            exact_match={"id": "1", "name": "Meta Ads"},
            possible_matches=[{"id": "2", "name": "Meta"}],
        )
        data = json.loads(r.model_dump_json())
        restored = IdentifySourceResult(**data)
        assert restored.exact_match["name"] == "Meta Ads"
        assert len(restored.possible_matches) == 1

    def test_register_request_roundtrip(self):
        req = RegisterSourceRequest(
            name="Meta Ads",
            protocol="file_upload",
            config={"key": "value"},
        )
        data = json.loads(req.model_dump_json())
        restored = RegisterSourceRequest(**data)
        assert restored.config["key"] == "value"


class TestManageSourceRegistryIntegration:
    def test_registry_includes_manage_source(self):
        from unlock_workers.registry import COMPONENTS

        cfg = COMPONENTS["data-manager"]
        workflow_names = {w.__name__ for w in cfg.workflows}
        assert "ManageSourceWorkflow" in workflow_names

    def test_registry_workflow_count(self):
        from unlock_workers.registry import COMPONENTS

        cfg = COMPONENTS["data-manager"]
        assert len(cfg.workflows) == 5

    def test_registry_has_identify_source(self):
        from unlock_workers.registry import COMPONENTS

        cfg = COMPONENTS["source-access"]
        activity_names = {a.__name__ for a in cfg.activities}
        assert "identify_source" in activity_names

    def test_registry_has_register_source(self):
        from unlock_workers.registry import COMPONENTS

        cfg = COMPONENTS["source-access"]
        activity_names = {a.__name__ for a in cfg.activities}
        assert "register_source" in activity_names
