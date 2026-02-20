"""Tests for Config Access activities — all 9 business verb activities.

Each test patches get_client() to return MockRedis, calls the activity,
and asserts the result. Tests are written BEFORE activities (test-first).

Pattern: unittest.mock.patch("unlock_config_access.activities.get_client")
returns MockRedis that records calls and stores data in-memory.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from unlock_shared.config_models import (
    ActivateViewRequest,
    ArchiveSchemaRequest,
    CloneViewRequest,
    DefinePipelineRequest,
    GrantAccessRequest,
    PublishSchemaRequest,
    RetrieveViewRequest,
    RevokeAccessRequest,
    SurveyConfigsRequest,
    TransformRule,
)

# ============================================================================
# publish_schema
# ============================================================================


class TestPublishSchema:
    @pytest.mark.asyncio
    async def test_publish_new_schema(self, mock_redis):
        from unlock_config_access.activities import publish_schema

        req = PublishSchemaRequest(
            name="Community Engagement Analysis",
            description="Tracks civic engagement",
            schema_type="funnel",
            created_by="paul",
        )

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await publish_schema(req)

        assert result.success is True
        assert result.schema_id != ""
        assert result.version == 1
        # Schema stored in Redis
        assert any(k.startswith("cfg:schema:") for k in mock_redis.store)

    @pytest.mark.asyncio
    async def test_publish_schema_version_increment(self, mock_redis):
        """Publishing a schema with an existing name creates a new version."""
        from unlock_config_access.activities import publish_schema

        req = PublishSchemaRequest(name="Versioned Schema", schema_type="analysis")

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result1 = await publish_schema(req)
            result2 = await publish_schema(req)

        assert result1.version == 1
        assert result2.version == 2
        assert result1.schema_id == result2.schema_id


# ============================================================================
# define_pipeline
# ============================================================================


class TestDefinePipeline:
    @pytest.mark.asyncio
    async def test_define_new_pipeline(self, mock_redis):
        from unlock_config_access.activities import define_pipeline

        req = DefinePipelineRequest(
            name="LinkedIn Post Ingestion",
            source_type="unipile",
            transform_rules=[TransformRule(rule_type="map", config={"source": "text"}, order=0)],
            created_by="paul",
        )

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await define_pipeline(req)

        assert result.success is True
        assert result.pipeline_id != ""
        assert result.version == 1

    @pytest.mark.asyncio
    async def test_define_pipeline_version_increment(self, mock_redis):
        from unlock_config_access.activities import define_pipeline

        req = DefinePipelineRequest(name="Pipeline V", source_type="x")

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            r1 = await define_pipeline(req)
            r2 = await define_pipeline(req)

        assert r1.version == 1
        assert r2.version == 2


# ============================================================================
# activate_view
# ============================================================================


class TestActivateView:
    @pytest.mark.asyncio
    async def test_activate_view_success(self, mock_redis):
        from unlock_config_access.activities import activate_view, publish_schema

        # First publish a schema so the reference is valid
        schema_req = PublishSchemaRequest(name="Test Schema")
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            schema_result = await publish_schema(schema_req)

        req = ActivateViewRequest(
            name="Alabama Dashboard",
            schema_id=schema_result.schema_id,
            filters={"state": "AL"},
            layout_config={"chart_type": "bar"},
            created_by="paul",
        )

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await activate_view(req)

        assert result.success is True
        assert result.view_id != ""
        assert result.share_token != ""

    @pytest.mark.asyncio
    async def test_activate_view_invalid_schema(self, mock_redis):
        from unlock_config_access.activities import activate_view

        req = ActivateViewRequest(
            name="Bad View",
            schema_id="nonexistent-schema-id",
        )

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await activate_view(req)

        assert result.success is False


# ============================================================================
# retrieve_view
# ============================================================================


class TestRetrieveView:
    @pytest.mark.asyncio
    async def test_retrieve_view_by_token(self, mock_redis):
        from unlock_config_access.activities import (
            activate_view,
            publish_schema,
            retrieve_view,
        )

        # Setup: publish schema + activate view
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            s = await publish_schema(PublishSchemaRequest(name="Schema"))
            v = await activate_view(
                ActivateViewRequest(name="View", schema_id=s.schema_id)
            )

        req = RetrieveViewRequest(share_token=v.share_token)
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await retrieve_view(req)

        assert result.success is True
        assert result.view is not None
        assert result.schema_def is not None

    @pytest.mark.asyncio
    async def test_retrieve_view_invalid_token(self, mock_redis):
        from unlock_config_access.activities import retrieve_view

        req = RetrieveViewRequest(share_token="invalid-token")
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await retrieve_view(req)

        assert result.success is False


# ============================================================================
# grant_access
# ============================================================================


class TestGrantAccess:
    @pytest.mark.asyncio
    async def test_grant_access_success(self, mock_redis):
        from unlock_config_access.activities import (
            activate_view,
            grant_access,
            publish_schema,
        )

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            s = await publish_schema(PublishSchemaRequest(name="Schema"))
            v = await activate_view(
                ActivateViewRequest(name="View", schema_id=s.schema_id)
            )

        req = GrantAccessRequest(
            view_id=v.view_id,
            principal_id="user-jane",
            principal_type="user",
            permission="read",
            granted_by="paul",
        )

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await grant_access(req)

        assert result.success is True
        assert result.granted is True
        # Permission stored in hash
        assert v.view_id in str(mock_redis.hashes)

    @pytest.mark.asyncio
    async def test_grant_access_invalid_view(self, mock_redis):
        from unlock_config_access.activities import grant_access

        req = GrantAccessRequest(
            view_id="nonexistent",
            principal_id="user-jane",
        )

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await grant_access(req)

        assert result.success is False


# ============================================================================
# revoke_access
# ============================================================================


class TestRevokeAccess:
    @pytest.mark.asyncio
    async def test_revoke_access_success(self, mock_redis):
        from unlock_config_access.activities import (
            activate_view,
            grant_access,
            publish_schema,
            revoke_access,
        )

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            s = await publish_schema(PublishSchemaRequest(name="Schema"))
            v = await activate_view(
                ActivateViewRequest(name="View", schema_id=s.schema_id)
            )
            await grant_access(
                GrantAccessRequest(view_id=v.view_id, principal_id="user-jane")
            )

        req = RevokeAccessRequest(view_id=v.view_id, principal_id="user-jane")
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await revoke_access(req)

        assert result.success is True
        assert result.revoked_count >= 1

    @pytest.mark.asyncio
    async def test_revoke_cascades_to_clones(self, mock_redis):
        """Revoking access on a parent view also revokes on cloned children."""
        from unlock_config_access.activities import (
            activate_view,
            clone_view,
            grant_access,
            publish_schema,
            revoke_access,
        )

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            s = await publish_schema(PublishSchemaRequest(name="Schema"))
            v = await activate_view(
                ActivateViewRequest(name="Parent View", schema_id=s.schema_id)
            )
            # Grant access, clone, then grant same principal on clone
            await grant_access(
                GrantAccessRequest(view_id=v.view_id, principal_id="user-jane")
            )
            clone = await clone_view(
                CloneViewRequest(
                    source_view_id=v.view_id, new_name="Child View"
                )
            )
            await grant_access(
                GrantAccessRequest(view_id=clone.view_id, principal_id="user-jane")
            )

        req = RevokeAccessRequest(view_id=v.view_id, principal_id="user-jane")
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await revoke_access(req)

        # Should revoke on parent + at least the clone
        assert result.revoked_count >= 2


# ============================================================================
# clone_view
# ============================================================================


class TestCloneView:
    @pytest.mark.asyncio
    async def test_clone_view_success(self, mock_redis):
        from unlock_config_access.activities import (
            activate_view,
            clone_view,
            publish_schema,
        )

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            s = await publish_schema(PublishSchemaRequest(name="Schema"))
            v = await activate_view(
                ActivateViewRequest(
                    name="Original",
                    schema_id=s.schema_id,
                    filters={"state": "AL"},
                )
            )

        req = CloneViewRequest(
            source_view_id=v.view_id,
            new_name="Cloned Dashboard",
            created_by="jane",
        )

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await clone_view(req)

        assert result.success is True
        assert result.view_id != v.view_id
        assert result.share_token != ""

        # Verify lineage: cloned view's JSON should reference the source
        cloned_json = mock_redis.store.get(f"cfg:view:{result.view_id}")
        assert cloned_json is not None
        cloned = json.loads(cloned_json)
        assert cloned["cloned_from"] == v.view_id

    @pytest.mark.asyncio
    async def test_clone_nonexistent_view(self, mock_redis):
        from unlock_config_access.activities import clone_view

        req = CloneViewRequest(source_view_id="nonexistent", new_name="Clone")
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await clone_view(req)

        assert result.success is False


# ============================================================================
# archive_schema
# ============================================================================


class TestArchiveSchema:
    @pytest.mark.asyncio
    async def test_archive_schema_no_deps(self, mock_redis):
        from unlock_config_access.activities import archive_schema, publish_schema

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            s = await publish_schema(PublishSchemaRequest(name="Orphan Schema"))

        req = ArchiveSchemaRequest(schema_id=s.schema_id)
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await archive_schema(req)

        assert result.success is True
        assert result.archived is True
        assert result.dependent_view_count == 0

        # Verify status changed in stored JSON
        stored = json.loads(mock_redis.store[f"cfg:schema:{s.schema_id}"])
        assert stored["status"] == "archived"

    @pytest.mark.asyncio
    async def test_archive_schema_with_deps(self, mock_redis):
        """Archiving a schema with dependent views still succeeds but reports count."""
        from unlock_config_access.activities import (
            activate_view,
            archive_schema,
            publish_schema,
        )

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            s = await publish_schema(PublishSchemaRequest(name="Used Schema"))
            await activate_view(
                ActivateViewRequest(name="View 1", schema_id=s.schema_id)
            )
            await activate_view(
                ActivateViewRequest(name="View 2", schema_id=s.schema_id)
            )

        req = ArchiveSchemaRequest(schema_id=s.schema_id)
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await archive_schema(req)

        assert result.success is True
        assert result.archived is True
        assert result.dependent_view_count == 2

    @pytest.mark.asyncio
    async def test_archive_nonexistent_schema(self, mock_redis):
        from unlock_config_access.activities import archive_schema

        req = ArchiveSchemaRequest(schema_id="nonexistent")
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await archive_schema(req)

        assert result.success is False


# ============================================================================
# survey_configs
# ============================================================================


class TestSurveyConfigs:
    @pytest.mark.asyncio
    async def test_survey_schemas(self, mock_redis):
        from unlock_config_access.activities import publish_schema, survey_configs

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            await publish_schema(PublishSchemaRequest(name="Schema A"))
            await publish_schema(PublishSchemaRequest(name="Schema B"))

        req = SurveyConfigsRequest(config_type="schema")
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await survey_configs(req)

        assert result.success is True
        assert result.total_count == 2
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_survey_pipelines(self, mock_redis):
        from unlock_config_access.activities import define_pipeline, survey_configs

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            await define_pipeline(
                DefinePipelineRequest(name="P1", source_type="unipile")
            )

        req = SurveyConfigsRequest(config_type="pipeline")
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await survey_configs(req)

        assert result.success is True
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_survey_views(self, mock_redis):
        from unlock_config_access.activities import (
            activate_view,
            publish_schema,
            survey_configs,
        )

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            s = await publish_schema(PublishSchemaRequest(name="Schema"))
            await activate_view(
                ActivateViewRequest(name="View A", schema_id=s.schema_id)
            )

        req = SurveyConfigsRequest(config_type="view")
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await survey_configs(req)

        assert result.success is True
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_survey_with_status_filter(self, mock_redis):
        from unlock_config_access.activities import publish_schema, survey_configs

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            await publish_schema(PublishSchemaRequest(name="Draft Schema"))

        req = SurveyConfigsRequest(config_type="schema", status="active")
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await survey_configs(req)

        # New schemas default to "draft" status, so "active" filter returns 0
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_survey_with_pagination(self, mock_redis):
        from unlock_config_access.activities import publish_schema, survey_configs

        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            for i in range(5):
                await publish_schema(PublishSchemaRequest(name=f"Schema {i}"))

        req = SurveyConfigsRequest(config_type="schema", limit=2, offset=0)
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await survey_configs(req)

        assert result.total_count == 5
        assert len(result.items) == 2
        assert result.has_more is True

    @pytest.mark.asyncio
    async def test_survey_invalid_config_type(self, mock_redis):
        from unlock_config_access.activities import survey_configs

        req = SurveyConfigsRequest(config_type="invalid")
        with patch("unlock_config_access.activities.get_client", return_value=mock_redis):
            result = await survey_configs(req)

        assert result.success is False


# ============================================================================
# hello_load_config (backward compat shim)
# ============================================================================


class TestHelloLoadConfig:
    @pytest.mark.asyncio
    async def test_shim_returns_string(self):
        from unlock_config_access.activities import hello_load_config

        result = await hello_load_config("test-key")
        assert "test-key" in result
