"""Tests for Data Manager workflows — structural verification.

Workflow integration tests (multi-queue activity dispatch) belong in INT_TEST.
Here we verify: correct Temporal decorators, model defaults, serialization
round-trips, and registry import integrity.
"""

from __future__ import annotations

import json

from unlock_data_manager.workflows.configure import ConfigureWorkflow
from unlock_data_manager.workflows.ingest import IngestWorkflow
from unlock_data_manager.workflows.query import QueryWorkflow
from unlock_data_manager.workflows.share import ShareWorkflow
from unlock_shared.manager_models import (
    ConfigureRequest,
    ConfigureResult,
    IngestRequest,
    IngestResult,
    QueryRequest,
    QueryResult,
    ShareRequest,
    ShareResult,
)
from unlock_shared.models import PlatformResult

# ============================================================================
# Workflow decoration
# ============================================================================


class TestWorkflowStructure:
    """Verify all four workflows are properly decorated for Temporal."""

    def test_ingest_is_decorated(self):
        assert hasattr(IngestWorkflow, "__temporal_workflow_definition")

    def test_query_is_decorated(self):
        assert hasattr(QueryWorkflow, "__temporal_workflow_definition")

    def test_configure_is_decorated(self):
        assert hasattr(ConfigureWorkflow, "__temporal_workflow_definition")

    def test_share_is_decorated(self):
        assert hasattr(ShareWorkflow, "__temporal_workflow_definition")

    def test_ingest_has_run(self):
        assert hasattr(IngestWorkflow(), "run")

    def test_query_has_run(self):
        assert hasattr(QueryWorkflow(), "run")

    def test_configure_has_run(self):
        assert hasattr(ConfigureWorkflow(), "run")

    def test_share_has_run(self):
        assert hasattr(ShareWorkflow(), "run")


# ============================================================================
# Request model defaults
# ============================================================================


class TestRequestDefaults:
    """Verify boundary model defaults match the design."""

    def test_ingest_request_defaults(self):
        req = IngestRequest(source_name="test", source_type="unipile")
        assert req.resource_type == "posts"
        assert req.channel_key is None
        assert req.auth_env_var is None
        assert req.base_url is None
        assert req.config_json is None
        assert req.since is None
        assert req.max_pages == 100

    def test_query_request_defaults(self):
        req = QueryRequest(share_token="tok-abc", user_id="u-1")
        assert req.user_type == "user"
        assert req.channel_key is None
        assert req.engagement_type is None
        assert req.since is None
        assert req.until is None
        assert req.limit == 100
        assert req.offset == 0

    def test_configure_request_defaults(self):
        req = ConfigureRequest(config_type="schema")
        assert req.name == ""
        assert req.description is None
        assert req.created_by is None
        assert req.schema_type == "analysis"
        assert req.fields == []
        assert req.funnel_stages == []
        assert req.source_type == ""
        assert req.transform_rules == []
        assert req.schedule_cron is None
        assert req.schema_id == ""
        assert req.filters == {}
        assert req.layout_config == {}

    def test_share_request_defaults(self):
        req = ShareRequest(
            share_token="tok-abc",
            granter_id="u-1",
            recipient_id="u-2",
        )
        assert req.recipient_type == "user"
        assert req.permission == "read"


# ============================================================================
# Result model defaults + PlatformResult inheritance
# ============================================================================


class TestResultDefaults:
    """Verify result model defaults and PlatformResult inheritance."""

    def test_ingest_result_defaults(self):
        r = IngestResult(success=True, message="ok")
        assert r.source_name == ""
        assert r.records_fetched == 0
        assert r.records_stored == 0
        assert r.records_transformed == 0
        assert r.pipeline_run_id == ""

    def test_ingest_result_is_platform_result(self):
        assert issubclass(IngestResult, PlatformResult)

    def test_query_result_defaults(self):
        r = QueryResult(success=True, message="ok")
        assert r.records == []
        assert r.total_count == 0
        assert r.has_more is False
        assert r.view_name == ""
        assert r.schema_id == ""

    def test_query_result_is_platform_result(self):
        assert issubclass(QueryResult, PlatformResult)

    def test_configure_result_defaults(self):
        r = ConfigureResult(success=True, message="ok")
        assert r.config_type == ""
        assert r.resource_id == ""
        assert r.version == 0
        assert r.share_token == ""

    def test_configure_result_is_platform_result(self):
        assert issubclass(ConfigureResult, PlatformResult)

    def test_share_result_defaults(self):
        r = ShareResult(success=True, message="ok")
        assert r.view_id == ""
        assert r.share_token == ""
        assert r.granted_permission == ""

    def test_share_result_is_platform_result(self):
        assert issubclass(ShareResult, PlatformResult)


# ============================================================================
# Serialization round-trips (Temporal JSON boundary)
# ============================================================================


class TestSerializationRoundTrips:
    """Verify models survive JSON serialization — the Temporal boundary."""

    def test_ingest_request_roundtrip(self):
        req = IngestRequest(source_name="src-1", source_type="unipile", max_pages=50)
        data = json.loads(req.model_dump_json())
        restored = IngestRequest(**data)
        assert restored.source_name == "src-1"
        assert restored.max_pages == 50

    def test_ingest_result_roundtrip(self):
        r = IngestResult(
            success=True,
            message="done",
            source_name="src-1",
            records_fetched=42,
            pipeline_run_id="run-001",
        )
        data = json.loads(r.model_dump_json())
        restored = IngestResult(**data)
        assert restored.records_fetched == 42
        assert restored.pipeline_run_id == "run-001"

    def test_query_request_roundtrip(self):
        req = QueryRequest(share_token="tok-1", user_id="u-1", limit=25)
        data = json.loads(req.model_dump_json())
        restored = QueryRequest(**data)
        assert restored.share_token == "tok-1"
        assert restored.limit == 25

    def test_configure_request_roundtrip(self):
        req = ConfigureRequest(
            config_type="pipeline",
            name="my-pipeline",
            source_type="unipile",
            transform_rules=[{"rule_type": "map", "config": {}, "order": 0}],
        )
        data = json.loads(req.model_dump_json())
        restored = ConfigureRequest(**data)
        assert restored.config_type == "pipeline"
        assert len(restored.transform_rules) == 1

    def test_share_request_roundtrip(self):
        req = ShareRequest(
            share_token="tok-1",
            granter_id="u-1",
            recipient_id="u-2",
            permission="write",
        )
        data = json.loads(req.model_dump_json())
        restored = ShareRequest(**data)
        assert restored.permission == "write"


# ============================================================================
# Registry integration
# ============================================================================


class TestRegistryIntegration:
    """Verify the registry imports all Data Manager components correctly."""

    def test_registry_has_data_manager(self):
        from unlock_workers.registry import COMPONENTS

        cfg = COMPONENTS["data-manager"]
        assert cfg.task_queue == "data-manager-queue"

    def test_registry_workflow_count(self):
        from unlock_workers.registry import COMPONENTS

        cfg = COMPONENTS["data-manager"]
        assert len(cfg.workflows) == 8

    def test_registry_no_activities(self):
        """Data Manager runs workflows only — activities live on engine/RA workers."""
        from unlock_workers.registry import COMPONENTS

        cfg = COMPONENTS["data-manager"]
        assert len(cfg.activities) == 0

    def test_registry_workflow_classes(self):
        from unlock_workers.registry import COMPONENTS

        cfg = COMPONENTS["data-manager"]
        workflow_names = {w.__name__ for w in cfg.workflows}
        assert workflow_names == {
            "IngestWorkflow",
            "QueryWorkflow",
            "ConfigureWorkflow",
            "ShareWorkflow",
            "ManageSourceWorkflow",
            "SurveyConfigsWorkflow",
            "RetrieveViewWorkflow",
            "RevokeAccessWorkflow",
        }
