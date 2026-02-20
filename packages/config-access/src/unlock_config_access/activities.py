"""Config Access activities — 9 business verb operations + backward-compat shim.

Run on CONFIG_ACCESS_QUEUE. Each activity uses the RedisAdapter for storage,
with JSON serialization for config objects and sorted sets/sets for indexes.

Business verbs follow the Righting Software test: "If I switched from Redis
to PostgreSQL, would this operation name still make sense?"
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from temporalio import activity
from unlock_shared.config_models import (
    ActivateViewRequest,
    ActivateViewResult,
    ArchiveSchemaRequest,
    ArchiveSchemaResult,
    CloneViewRequest,
    CloneViewResult,
    DefinePipelineRequest,
    DefinePipelineResult,
    GrantAccessRequest,
    GrantAccessResult,
    PublishSchemaRequest,
    PublishSchemaResult,
    RetrieveViewRequest,
    RetrieveViewResult,
    RevokeAccessRequest,
    RevokeAccessResult,
    SchemaDefinition,
    SurveyConfigsRequest,
    SurveyConfigsResult,
    ViewDefinition,
    ViewPermission,
)

from unlock_config_access import keys as k  # noqa: E402 — for pipeline name lookup
from unlock_config_access.client import get_client
from unlock_config_access.keys import (
    perm_idx_principal,
    perm_key,
    pipeline_idx_all,
    pipeline_idx_source,
    pipeline_idx_status,
    pipeline_key,
    pipeline_version_key,
    schema_idx_all,
    schema_idx_name,
    schema_idx_status,
    schema_key,
    schema_version_key,
    view_idx_all,
    view_idx_clones,
    view_idx_schema,
    view_idx_status,
    view_idx_token,
    view_key,
)

# ============================================================================
# publish_schema
# ============================================================================


@activity.defn
async def publish_schema(request: PublishSchemaRequest) -> PublishSchemaResult:
    """Validate, version, and store a schema definition."""
    try:
        client = get_client()
        now = datetime.now(UTC)
        ts = now.timestamp()

        # Check if schema with this name already exists (version increment)
        existing_id = await client.get(schema_idx_name(request.name))

        if existing_id:
            # Load existing to get current version
            existing_json = await client.get(schema_key(existing_id))
            if existing_json:
                existing = json.loads(existing_json)
                version = existing.get("version", 0) + 1
                schema_id = existing_id
            else:
                version = 1
                schema_id = str(uuid.uuid4())
        else:
            version = 1
            schema_id = str(uuid.uuid4())

        schema = SchemaDefinition(
            id=schema_id,
            name=request.name,
            description=request.description,
            version=version,
            status="draft",
            schema_type=request.schema_type,
            fields=request.fields,
            funnel_stages=request.funnel_stages,
            created_at=now,
            updated_at=now,
            created_by=request.created_by,
        )

        schema_json = schema.model_dump_json()

        # Store current version + immutable snapshot
        await client.set(schema_key(schema_id), schema_json)
        await client.set(schema_version_key(schema_id, version), schema_json)

        # Update indexes
        await client.set(schema_idx_name(request.name), schema_id)
        await client.zadd(schema_idx_all(), {schema_id: ts})
        await client.sadd(schema_idx_status("draft"), schema_id)

        return PublishSchemaResult(
            success=True,
            message=f"Schema '{request.name}' v{version} published",
            schema_id=schema_id,
            version=version,
        )
    except Exception as e:
        return PublishSchemaResult(
            success=False, message=f"publish_schema failed: {e}"
        )


# ============================================================================
# define_pipeline
# ============================================================================


@activity.defn
async def define_pipeline(request: DefinePipelineRequest) -> DefinePipelineResult:
    """Register a transformation pipeline for a source type."""
    try:
        client = get_client()
        now = datetime.now(UTC)
        ts = now.timestamp()

        # Check if pipeline for this source_type already exists
        existing_id = await client.get(pipeline_idx_source(request.source_type))

        if existing_id:
            existing_json = await client.get(pipeline_key(existing_id))
            if existing_json:
                existing = json.loads(existing_json)
                version = existing.get("version", 0) + 1
                pipeline_id = existing_id
            else:
                version = 1
                pipeline_id = str(uuid.uuid4())
        else:
            version = 1
            pipeline_id = str(uuid.uuid4())

        pipeline_data = {
            "id": pipeline_id,
            "name": request.name,
            "description": request.description,
            "version": version,
            "status": "draft",
            "source_type": request.source_type,
            "transform_rules": [r.model_dump() for r in request.transform_rules],
            "schedule_cron": request.schedule_cron,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "created_by": request.created_by,
        }

        pipeline_json = json.dumps(pipeline_data)

        await client.set(pipeline_key(pipeline_id), pipeline_json)
        await client.set(pipeline_version_key(pipeline_id, version), pipeline_json)

        # Update indexes
        await client.set(pipeline_idx_source(request.source_type), pipeline_id)
        await client.zadd(pipeline_idx_all(), {pipeline_id: ts})
        await client.sadd(pipeline_idx_status("draft"), pipeline_id)

        return DefinePipelineResult(
            success=True,
            message=f"Pipeline '{request.name}' v{version} defined",
            pipeline_id=pipeline_id,
            version=version,
        )
    except Exception as e:
        return DefinePipelineResult(
            success=False, message=f"define_pipeline failed: {e}"
        )


# ============================================================================
# activate_view
# ============================================================================


@activity.defn
async def activate_view(request: ActivateViewRequest) -> ActivateViewResult:
    """Create/update a view, validate schema reference, generate share token."""
    try:
        client = get_client()
        now = datetime.now(UTC)
        ts = now.timestamp()

        # Validate schema exists
        schema_json = await client.get(schema_key(request.schema_id))
        if not schema_json:
            return ActivateViewResult(
                success=False,
                message=f"Schema not found: {request.schema_id}",
            )

        view_id = str(uuid.uuid4())
        share_token = str(uuid.uuid4())

        view = ViewDefinition(
            id=view_id,
            name=request.name,
            description=request.description,
            schema_id=request.schema_id,
            status="active",
            share_token=share_token,
            filters=request.filters,
            layout_config=request.layout_config,
            created_at=now,
            updated_at=now,
            created_by=request.created_by,
        )

        view_json = view.model_dump_json()

        await client.set(view_key(view_id), view_json)

        # Update indexes
        await client.set(view_idx_token(share_token), view_id)
        await client.zadd(view_idx_all(), {view_id: ts})
        await client.sadd(view_idx_schema(request.schema_id), view_id)
        await client.sadd(view_idx_status("active"), view_id)

        return ActivateViewResult(
            success=True,
            message=f"View '{request.name}' activated",
            view_id=view_id,
            share_token=share_token,
        )
    except Exception as e:
        return ActivateViewResult(
            success=False, message=f"activate_view failed: {e}"
        )


# ============================================================================
# retrieve_view
# ============================================================================


@activity.defn
async def retrieve_view(request: RetrieveViewRequest) -> RetrieveViewResult:
    """Assemble a complete view by share token: view + schema + permissions."""
    try:
        client = get_client()

        # Look up view ID from share token
        view_id = await client.get(view_idx_token(request.share_token))
        if not view_id:
            return RetrieveViewResult(
                success=False, message="View not found for token"
            )

        # Load view
        view_json = await client.get(view_key(view_id))
        if not view_json:
            return RetrieveViewResult(
                success=False, message="View data not found"
            )

        view_data = json.loads(view_json)

        # Load schema
        schema_id = view_data.get("schema_id", "")
        schema_json = await client.get(schema_key(schema_id))
        schema_data = json.loads(schema_json) if schema_json else None

        # Load permissions
        perm_hash = await client.hgetall(perm_key(view_id))
        permissions = []
        for _principal_id, perm_json in perm_hash.items():
            permissions.append(json.loads(perm_json))

        return RetrieveViewResult(
            success=True,
            message="View retrieved",
            view=view_data,
            schema_def=schema_data,
            permissions=permissions,
        )
    except Exception as e:
        return RetrieveViewResult(
            success=False, message=f"retrieve_view failed: {e}"
        )


# ============================================================================
# grant_access
# ============================================================================


@activity.defn
async def grant_access(request: GrantAccessRequest) -> GrantAccessResult:
    """Add permission on a view for a principal."""
    try:
        client = get_client()
        now = datetime.now(UTC)

        # Validate view exists
        view_json = await client.get(view_key(request.view_id))
        if not view_json:
            return GrantAccessResult(
                success=False, message=f"View not found: {request.view_id}"
            )

        perm = ViewPermission(
            view_id=request.view_id,
            principal_id=request.principal_id,
            principal_type=request.principal_type,
            permission=request.permission,
            granted_at=now,
            granted_by=request.granted_by,
        )

        perm_json = perm.model_dump_json()

        # Store in hash: perm:{view_id} → {principal_id: JSON}
        await client.hset(perm_key(request.view_id), request.principal_id, perm_json)
        # Index: principal → set of view IDs
        await client.sadd(perm_idx_principal(request.principal_id), request.view_id)

        return GrantAccessResult(
            success=True,
            message=f"Access granted to {request.principal_id}",
            granted=True,
        )
    except Exception as e:
        return GrantAccessResult(
            success=False, message=f"grant_access failed: {e}"
        )


# ============================================================================
# revoke_access
# ============================================================================


@activity.defn
async def revoke_access(request: RevokeAccessRequest) -> RevokeAccessResult:
    """Remove permission, cascade to cloned child views."""
    try:
        client = get_client()
        revoked = 0

        # Revoke on the target view
        existing = await client.hget(perm_key(request.view_id), request.principal_id)
        if existing:
            await client.hdel(perm_key(request.view_id), request.principal_id)
            await client.srem(
                perm_idx_principal(request.principal_id), request.view_id
            )
            revoked += 1

        # Cascade to clones
        clone_ids = await client.smembers(view_idx_clones(request.view_id))
        for clone_id in clone_ids:
            clone_existing = await client.hget(perm_key(clone_id), request.principal_id)
            if clone_existing:
                await client.hdel(perm_key(clone_id), request.principal_id)
                await client.srem(
                    perm_idx_principal(request.principal_id), clone_id
                )
                revoked += 1

        return RevokeAccessResult(
            success=True,
            message=f"Revoked {revoked} permissions",
            revoked_count=revoked,
        )
    except Exception as e:
        return RevokeAccessResult(
            success=False, message=f"revoke_access failed: {e}"
        )


# ============================================================================
# clone_view
# ============================================================================


@activity.defn
async def clone_view(request: CloneViewRequest) -> CloneViewResult:
    """Deep copy a view with lineage tracking and inherited base permissions."""
    try:
        client = get_client()
        now = datetime.now(UTC)
        ts = now.timestamp()

        # Load source view
        source_json = await client.get(view_key(request.source_view_id))
        if not source_json:
            return CloneViewResult(
                success=False,
                message=f"Source view not found: {request.source_view_id}",
            )

        source = json.loads(source_json)

        clone_id = str(uuid.uuid4())
        clone_token = str(uuid.uuid4())

        cloned_view = ViewDefinition(
            id=clone_id,
            name=request.new_name,
            description=source.get("description"),
            schema_id=source.get("schema_id", ""),
            status="active",
            share_token=clone_token,
            filters=source.get("filters", {}),
            layout_config=source.get("layout_config", {}),
            cloned_from=request.source_view_id,
            created_at=now,
            updated_at=now,
            created_by=request.created_by,
        )

        clone_json = cloned_view.model_dump_json()

        await client.set(view_key(clone_id), clone_json)

        # Update indexes
        await client.set(view_idx_token(clone_token), clone_id)
        await client.zadd(view_idx_all(), {clone_id: ts})
        await client.sadd(view_idx_schema(source.get("schema_id", "")), clone_id)
        await client.sadd(view_idx_status("active"), clone_id)
        await client.sadd(view_idx_clones(request.source_view_id), clone_id)

        # Inherit permissions from source
        source_perms = await client.hgetall(perm_key(request.source_view_id))
        for principal_id, perm_json in source_perms.items():
            perm_data = json.loads(perm_json)
            perm_data["view_id"] = clone_id
            await client.hset(
                perm_key(clone_id), principal_id, json.dumps(perm_data)
            )
            await client.sadd(perm_idx_principal(principal_id), clone_id)

        return CloneViewResult(
            success=True,
            message=f"View cloned as '{request.new_name}'",
            view_id=clone_id,
            share_token=clone_token,
        )
    except Exception as e:
        return CloneViewResult(
            success=False, message=f"clone_view failed: {e}"
        )


# ============================================================================
# archive_schema
# ============================================================================


@activity.defn
async def archive_schema(request: ArchiveSchemaRequest) -> ArchiveSchemaResult:
    """Soft delete a schema, check dependent views."""
    try:
        client = get_client()

        # Load schema
        schema_json = await client.get(schema_key(request.schema_id))
        if not schema_json:
            return ArchiveSchemaResult(
                success=False,
                message=f"Schema not found: {request.schema_id}",
            )

        # Count dependent views
        dependent_views = await client.smembers(
            view_idx_schema(request.schema_id)
        )
        dep_count = len(dependent_views)

        # Update schema status to archived
        schema_data = json.loads(schema_json)
        old_status = schema_data.get("status", "draft")
        schema_data["status"] = "archived"
        schema_data["updated_at"] = datetime.now(UTC).isoformat()

        await client.set(schema_key(request.schema_id), json.dumps(schema_data))

        # Update status indexes
        await client.srem(schema_idx_status(old_status), request.schema_id)
        await client.sadd(schema_idx_status("archived"), request.schema_id)

        return ArchiveSchemaResult(
            success=True,
            message=f"Schema archived ({dep_count} dependent views)",
            archived=True,
            dependent_view_count=dep_count,
        )
    except Exception as e:
        return ArchiveSchemaResult(
            success=False, message=f"archive_schema failed: {e}"
        )


# ============================================================================
# survey_configs
# ============================================================================


@activity.defn
async def survey_configs(request: SurveyConfigsRequest) -> SurveyConfigsResult:
    """List/search schemas, pipelines, or views with filters."""
    try:
        client = get_client()

        # Determine which index to query
        if request.config_type == "schema":
            if request.status:
                member_ids = await client.smembers(
                    schema_idx_status(request.status)
                )
                all_ids = list(member_ids)
            else:
                all_ids = await client.zrange(
                    schema_idx_all(), 0, -1
                )
            key_fn = k.schema_key
        elif request.config_type == "pipeline":
            if request.status:
                member_ids = await client.smembers(
                    pipeline_idx_status(request.status)
                )
                all_ids = list(member_ids)
            else:
                all_ids = await client.zrange(
                    pipeline_idx_all(), 0, -1
                )
            key_fn = k.pipeline_key
        elif request.config_type == "view":
            if request.status:
                member_ids = await client.smembers(
                    view_idx_status(request.status)
                )
                all_ids = list(member_ids)
            else:
                all_ids = await client.zrange(
                    view_idx_all(), 0, -1
                )
            key_fn = k.view_key
        else:
            return SurveyConfigsResult(
                success=False,
                message=f"Invalid config_type: {request.config_type}",
            )

        total_count = len(all_ids)

        # Apply name filter if provided
        if request.name_pattern:
            pattern = request.name_pattern.lower()
            filtered = []
            for item_id in all_ids:
                item_json = await client.get(key_fn(item_id))
                if item_json:
                    item_data = json.loads(item_json)
                    if pattern in item_data.get("name", "").lower():
                        filtered.append(item_id)
            all_ids = filtered
            total_count = len(all_ids)

        # Paginate
        page_ids = all_ids[request.offset:request.offset + request.limit]
        has_more = (request.offset + request.limit) < total_count

        # Load items
        items = []
        for item_id in page_ids:
            item_json = await client.get(key_fn(item_id))
            if item_json:
                items.append(json.loads(item_json))

        return SurveyConfigsResult(
            success=True,
            message=f"Found {total_count} {request.config_type}(s)",
            items=items,
            total_count=total_count,
            has_more=has_more,
        )
    except Exception as e:
        return SurveyConfigsResult(
            success=False, message=f"survey_configs failed: {e}"
        )


# ============================================================================
# hello_load_config (backward compatibility shim)
# ============================================================================


@activity.defn
async def hello_load_config(config_key: str) -> str:
    """Deprecated: simulates loading a pipeline configuration.

    Kept for backward compatibility with ConfigureWorkflow which calls this
    activity on CONFIG_ACCESS_QUEUE. Will be replaced when DATA_MGR wires
    workflows to the new business verb activities.
    """
    activity.logger.info(f"Config Access: loading config '{config_key}'")
    return f"Config loaded: {config_key}"
