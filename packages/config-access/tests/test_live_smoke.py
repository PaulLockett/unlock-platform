"""Live smoke tests against a real Upstash Redis preview database.

These run in the Upstash Bot workflow against the PR's ephemeral database.
They verify that mocked behavior in test_activities.py matches real Upstash
Redis behavior — catching adapter differences (zadd format, hgetall return
type, zrange semantics, etc.) that mocks can't surface.

Skipped automatically when UPSTASH_REDIS_REST_URL is not set, so they
never run in regular CI or local dev (unless you point at a real DB).
"""

from __future__ import annotations

import os
import uuid

import pytest
from unlock_config_access.client import reset_client

SKIP = not os.environ.get("UPSTASH_REDIS_REST_URL")
REASON = "UPSTASH_REDIS_REST_URL not set — requires Upstash preview database"

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(SKIP, reason=REASON),
]

# Unique prefix per test run so parallel/repeated runs don't collide.
# The PR database is destroyed on close anyway.
RUN = uuid.uuid4().hex[:8]


@pytest.fixture(autouse=True)
def _live_client():
    """Reset client singleton so get_client() picks up real Upstash env vars."""
    reset_client()
    yield
    reset_client()


# ============================================================================
# Schema lifecycle
# ============================================================================


class TestLiveSchema:
    @pytest.mark.asyncio
    async def test_publish_and_survey(self):
        """publish_schema → survey_configs → find it."""
        from unlock_config_access.activities import publish_schema, survey_configs
        from unlock_shared.config_models import PublishSchemaRequest, SurveyConfigsRequest

        name = f"smoke-schema-{RUN}"
        result = await publish_schema(PublishSchemaRequest(
            name=name, schema_type="analysis", created_by="smoke-test",
        ))
        assert result.success, f"publish_schema failed: {result.message}"
        assert result.schema_id
        assert result.version == 1

        survey = await survey_configs(SurveyConfigsRequest(config_type="schema"))
        assert survey.success
        names = [item["name"] for item in survey.items]
        assert name in names

    @pytest.mark.asyncio
    async def test_version_increment(self):
        """Publishing the same name twice increments the version."""
        from unlock_config_access.activities import publish_schema
        from unlock_shared.config_models import PublishSchemaRequest

        name = f"smoke-versioned-{RUN}"
        r1 = await publish_schema(PublishSchemaRequest(name=name))
        r2 = await publish_schema(PublishSchemaRequest(name=name))
        assert r1.version == 1
        assert r2.version == 2
        assert r1.schema_id == r2.schema_id

    @pytest.mark.asyncio
    async def test_archive_schema(self):
        """publish → archive → verify status."""
        from unlock_config_access.activities import archive_schema, publish_schema
        from unlock_shared.config_models import ArchiveSchemaRequest, PublishSchemaRequest

        s = await publish_schema(PublishSchemaRequest(name=f"smoke-archive-{RUN}"))
        assert s.success

        result = await archive_schema(ArchiveSchemaRequest(schema_id=s.schema_id))
        assert result.success
        assert result.archived


# ============================================================================
# Pipeline
# ============================================================================


class TestLivePipeline:
    @pytest.mark.asyncio
    async def test_define_pipeline(self):
        from unlock_config_access.activities import define_pipeline
        from unlock_shared.config_models import DefinePipelineRequest

        result = await define_pipeline(DefinePipelineRequest(
            name=f"smoke-pipeline-{RUN}",
            source_type=f"test-{RUN}",
            created_by="smoke-test",
        ))
        assert result.success, f"define_pipeline failed: {result.message}"
        assert result.pipeline_id
        assert result.version == 1


# ============================================================================
# View lifecycle: activate → retrieve → clone
# ============================================================================


class TestLiveViewLifecycle:
    @pytest.mark.asyncio
    async def test_activate_retrieve_clone(self):
        """Full lifecycle: schema → view → retrieve by token → clone with lineage."""
        from unlock_config_access.activities import (
            activate_view,
            clone_view,
            publish_schema,
            retrieve_view,
        )
        from unlock_shared.config_models import (
            ActivateViewRequest,
            CloneViewRequest,
            PublishSchemaRequest,
            RetrieveViewRequest,
        )

        # Publish schema (views reference schemas)
        schema = await publish_schema(PublishSchemaRequest(
            name=f"smoke-view-schema-{RUN}", schema_type="analysis",
        ))
        assert schema.success

        # Activate view
        view = await activate_view(ActivateViewRequest(
            name=f"smoke-view-{RUN}",
            schema_id=schema.schema_id,
            filters={"state": "AL"},
            created_by="smoke-test",
        ))
        assert view.success, f"activate_view failed: {view.message}"
        assert view.share_token

        # Retrieve by share token
        retrieved = await retrieve_view(RetrieveViewRequest(
            share_token=view.share_token,
        ))
        assert retrieved.success, f"retrieve_view failed: {retrieved.message}"
        assert retrieved.view is not None
        assert retrieved.view["name"] == f"smoke-view-{RUN}"
        assert retrieved.schema_def is not None

        # Clone with lineage
        cloned = await clone_view(CloneViewRequest(
            source_view_id=view.view_id,
            new_name=f"smoke-clone-{RUN}",
            created_by="smoke-test",
        ))
        assert cloned.success, f"clone_view failed: {cloned.message}"
        assert cloned.view_id != view.view_id
        assert cloned.share_token != view.share_token

        # Verify clone is retrievable
        clone_data = await retrieve_view(RetrieveViewRequest(
            share_token=cloned.share_token,
        ))
        assert clone_data.success
        assert clone_data.view["cloned_from"] == view.view_id


# ============================================================================
# Permissions: grant → verify → revoke → verify gone
# ============================================================================


class TestLivePermissions:
    @pytest.mark.asyncio
    async def test_grant_and_revoke(self):
        """Full permission lifecycle on a real Upstash hash."""
        from unlock_config_access.activities import (
            activate_view,
            grant_access,
            publish_schema,
            retrieve_view,
            revoke_access,
        )
        from unlock_shared.config_models import (
            ActivateViewRequest,
            GrantAccessRequest,
            PublishSchemaRequest,
            RetrieveViewRequest,
            RevokeAccessRequest,
        )

        # Setup
        schema = await publish_schema(PublishSchemaRequest(
            name=f"smoke-perm-schema-{RUN}",
        ))
        view = await activate_view(ActivateViewRequest(
            name=f"smoke-perm-view-{RUN}",
            schema_id=schema.schema_id,
        ))

        # Grant
        grant = await grant_access(GrantAccessRequest(
            view_id=view.view_id,
            principal_id=f"user-{RUN}",
            permission="read",
        ))
        assert grant.success, f"grant_access failed: {grant.message}"
        assert grant.granted

        # Verify permission appears in retrieve
        retrieved = await retrieve_view(RetrieveViewRequest(
            share_token=view.share_token,
        ))
        assert len(retrieved.permissions) == 1
        assert retrieved.permissions[0]["principal_id"] == f"user-{RUN}"

        # Revoke
        revoked = await revoke_access(RevokeAccessRequest(
            view_id=view.view_id,
            principal_id=f"user-{RUN}",
        ))
        assert revoked.success, f"revoke_access failed: {revoked.message}"
        assert revoked.revoked_count == 1

        # Verify permission gone
        after = await retrieve_view(RetrieveViewRequest(
            share_token=view.share_token,
        ))
        assert len(after.permissions) == 0
