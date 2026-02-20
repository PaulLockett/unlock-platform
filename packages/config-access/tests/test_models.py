"""Tests for Config Access boundary models.

Validates:
  - All model fields have correct types and defaults
  - Pydantic serialization/deserialization works
  - PlatformResult inheritance chain
  - Domain objects serialize to JSON correctly
"""

from unlock_shared.config_models import (
    ActivateViewRequest,
    ActivateViewResult,
    ArchiveSchemaRequest,
    ArchiveSchemaResult,
    CloneViewRequest,
    CloneViewResult,
    DefinePipelineRequest,
    DefinePipelineResult,
    FieldMapping,
    FunnelStage,
    GrantAccessRequest,
    GrantAccessResult,
    PipelineDefinition,
    PublishSchemaRequest,
    PublishSchemaResult,
    RetrieveViewRequest,
    RetrieveViewResult,
    RevokeAccessRequest,
    RevokeAccessResult,
    SchemaDefinition,
    SurveyConfigsRequest,
    SurveyConfigsResult,
    TransformRule,
    ViewDefinition,
    ViewPermission,
)
from unlock_shared.models import PlatformResult


class TestDomainObjects:
    """Domain objects must serialize/deserialize correctly."""

    def test_field_mapping_defaults(self):
        fm = FieldMapping(source_field="text", target_field="body")
        assert fm.source_field == "text"
        assert fm.target_field == "body"
        assert fm.transform is None
        assert fm.default_value is None

    def test_field_mapping_with_transform(self):
        fm = FieldMapping(
            source_field="name",
            target_field="display_name",
            transform="lowercase",
            default_value="Unknown",
        )
        assert fm.transform == "lowercase"
        assert fm.default_value == "Unknown"

    def test_transform_rule_defaults(self):
        tr = TransformRule(rule_type="map")
        assert tr.rule_type == "map"
        assert tr.config == {}
        assert tr.order == 0

    def test_funnel_stage_defaults(self):
        fs = FunnelStage(name="Awareness")
        assert fs.name == "Awareness"
        assert fs.description is None
        assert fs.order == 0

    def test_schema_definition_defaults(self):
        sd = SchemaDefinition(name="Test Schema")
        assert sd.name == "Test Schema"
        assert sd.version == 1
        assert sd.status == "draft"
        assert sd.schema_type == "analysis"
        assert sd.fields == []
        assert sd.funnel_stages == []

    def test_schema_definition_full(self):
        sd = SchemaDefinition(
            id="schema-1",
            name="Engagement Funnel",
            description="Tracks civic engagement progression",
            version=3,
            status="active",
            schema_type="funnel",
            fields=[FieldMapping(source_field="a", target_field="b")],
            funnel_stages=[FunnelStage(name="Stage 1", order=0)],
            created_by="paul",
        )
        assert sd.version == 3
        assert len(sd.fields) == 1
        assert len(sd.funnel_stages) == 1

    def test_pipeline_definition_defaults(self):
        pd = PipelineDefinition(name="Test Pipeline", source_type="unipile")
        assert pd.source_type == "unipile"
        assert pd.version == 1
        assert pd.status == "draft"
        assert pd.transform_rules == []

    def test_view_definition_defaults(self):
        vd = ViewDefinition(name="Test View")
        assert vd.schema_id == ""
        assert vd.status == "draft"
        assert vd.share_token is None
        assert vd.cloned_from is None

    def test_view_permission_defaults(self):
        vp = ViewPermission(view_id="v1", principal_id="user-1")
        assert vp.principal_type == "user"
        assert vp.permission == "read"

    def test_schema_serialization_roundtrip(self):
        sd = SchemaDefinition(
            id="s1",
            name="Test",
            fields=[FieldMapping(source_field="a", target_field="b")],
        )
        json_str = sd.model_dump_json()
        restored = SchemaDefinition.model_validate_json(json_str)
        assert restored.name == sd.name
        assert restored.fields[0].source_field == "a"


class TestRequestResultPairs:
    """Every Result must extend PlatformResult; Requests must have correct fields."""

    def test_publish_schema_request(self):
        req = PublishSchemaRequest(name="My Schema", schema_type="funnel")
        assert req.name == "My Schema"
        assert req.schema_type == "funnel"

    def test_publish_schema_result_extends_platform_result(self):
        result = PublishSchemaResult(success=True, message="ok", schema_id="s1", version=1)
        assert isinstance(result, PlatformResult)
        assert result.schema_id == "s1"
        assert result.version == 1

    def test_define_pipeline_request(self):
        req = DefinePipelineRequest(name="LinkedIn Pipeline", source_type="unipile")
        assert req.source_type == "unipile"

    def test_define_pipeline_result_defaults(self):
        result = DefinePipelineResult(success=True, message="ok")
        assert result.pipeline_id == ""
        assert result.version == 0

    def test_activate_view_request(self):
        req = ActivateViewRequest(name="Dashboard", schema_id="s1")
        assert req.schema_id == "s1"

    def test_activate_view_result(self):
        result = ActivateViewResult(
            success=True, message="ok", view_id="v1", share_token="abc123"
        )
        assert result.share_token == "abc123"

    def test_retrieve_view_request(self):
        req = RetrieveViewRequest(share_token="abc123")
        assert req.share_token == "abc123"

    def test_retrieve_view_result(self):
        result = RetrieveViewResult(success=True, message="ok")
        assert result.view is None
        assert result.schema_def is None
        assert result.permissions == []

    def test_grant_access_request(self):
        req = GrantAccessRequest(view_id="v1", principal_id="user-1")
        assert req.principal_type == "user"
        assert req.permission == "read"

    def test_grant_access_result(self):
        result = GrantAccessResult(success=True, message="ok", granted=True)
        assert result.granted is True

    def test_revoke_access_request(self):
        req = RevokeAccessRequest(view_id="v1", principal_id="user-1")
        assert req.view_id == "v1"

    def test_revoke_access_result(self):
        result = RevokeAccessResult(success=True, message="ok", revoked_count=3)
        assert result.revoked_count == 3

    def test_clone_view_request(self):
        req = CloneViewRequest(source_view_id="v1", new_name="Copy of Dashboard")
        assert req.new_name == "Copy of Dashboard"

    def test_clone_view_result(self):
        result = CloneViewResult(
            success=True, message="ok", view_id="v2", share_token="xyz789"
        )
        assert result.view_id == "v2"

    def test_archive_schema_request(self):
        req = ArchiveSchemaRequest(schema_id="s1")
        assert req.schema_id == "s1"

    def test_archive_schema_result(self):
        result = ArchiveSchemaResult(
            success=True, message="ok", archived=True, dependent_view_count=2
        )
        assert result.dependent_view_count == 2

    def test_survey_configs_request(self):
        req = SurveyConfigsRequest(config_type="schema", status="active")
        assert req.config_type == "schema"
        assert req.limit == 100
        assert req.offset == 0

    def test_survey_configs_result(self):
        result = SurveyConfigsResult(
            success=True, message="ok", items=[{"id": "s1"}], total_count=1
        )
        assert result.total_count == 1
        assert result.has_more is False
