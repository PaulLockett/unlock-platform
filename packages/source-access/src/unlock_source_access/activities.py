"""Source Access activities — Temporal activity functions for external data sources.

These run on the source-access worker (SOURCE_ACCESS_QUEUE). The Data Manager's
workflows dispatch to this queue when they need to interact with external data
sources (APIs, files, scraped content).

Business verbs (renamed from CRUD):
  verify_source    — verify connectivity, return API metadata
  harvest_records  — fetch records with auto-pagination
  probe_source     — lightweight credential validation
  discover_schema  — discover source field names/types from a sample

Deprecated aliases kept for backward compatibility:
  connect_source    → verify_source
  fetch_source_data → harvest_records
  test_connection   → probe_source
  get_source_schema → discover_schema
"""

import os

from temporalio import activity
from unlock_shared.source_models import (
    ConnectionResult,
    FetchRequest,
    FetchResult,
    IdentifySourceRequest,
    IdentifySourceResult,
    RegisterSourceRequest,
    RegisterSourceResult,
    SourceConfig,
    SourceSchema,
)

from unlock_source_access.connectors import get_connector

# ---------------------------------------------------------------------------
# Business verb activities
# ---------------------------------------------------------------------------


@activity.defn
async def verify_source(config: SourceConfig) -> ConnectionResult:
    """Verify connectivity to an external data source and return API metadata.

    Used by IngestWorkflow to validate a source before fetching, and by
    ConfigureWorkflow to verify a newly-added source configuration.
    """
    activity.logger.info(
        f"Connecting to {config.source_type} source '{config.source_id}'",
    )
    connector = get_connector(config)
    try:
        return await connector.connect()
    finally:
        await connector.close()


@activity.defn
async def harvest_records(request: FetchRequest) -> FetchResult:
    """Pull data from an external source with auto-pagination.

    This is the workhorse activity — it handles pagination internally using
    activity.heartbeat() to signal liveness during long runs. All records are
    collected and returned as list[dict] for Temporal serialization.
    """
    config = SourceConfig(
        source_id=request.source_id,
        source_type=request.source_type,
        base_url=request.base_url,
        auth_env_var=request.auth_env_var,
        config_json=request.config_json,
        rate_limit_per_second=request.rate_limit_per_second,
    )
    activity.logger.info(
        f"Fetching {request.resource_type} from {config.source_type} "
        f"source '{config.source_id}'",
    )
    connector = get_connector(config)
    try:
        return await connector.fetch_data(request)
    finally:
        await connector.close()


@activity.defn
async def probe_source(config: SourceConfig) -> ConnectionResult:
    """Lightweight credential check for a data source.

    Functionally identical to verify_source but semantically distinct —
    used by ConfigureWorkflow when the user wants a quick "does this work?"
    check without committing to a full connection setup.
    """
    activity.logger.info(
        f"Testing connection to {config.source_type} "
        f"source '{config.source_id}'",
    )
    connector = get_connector(config)
    try:
        return await connector.test_connection()
    finally:
        await connector.close()


@activity.defn
async def discover_schema(request: FetchRequest) -> SourceSchema:
    """Discover field names and types from a sample of source data.

    Used by Schema Engine to understand the shape of a source before
    building transformation pipelines.
    """
    config = SourceConfig(
        source_id=request.source_id,
        source_type=request.source_type,
        base_url=request.base_url,
        auth_env_var=request.auth_env_var,
        config_json=request.config_json,
        rate_limit_per_second=request.rate_limit_per_second,
    )
    activity.logger.info(
        f"Discovering schema for {config.source_type} "
        f"source '{config.source_id}'",
    )
    connector = get_connector(config)
    try:
        return await connector.get_schema(request)
    finally:
        await connector.close()


# ---------------------------------------------------------------------------
# Source registry activities — identify and register data sources
# ---------------------------------------------------------------------------


def _get_supabase_client():
    """Create a Supabase client for source registry operations."""
    from supabase import create_client

    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


@activity.defn
async def identify_source(request: IdentifySourceRequest) -> IdentifySourceResult:
    """Have we seen this source before? What matches?

    If name is provided: exact match lookup + partial matches.
    If name is None: return all known sources (the "list" use case).
    """
    activity.logger.info(f"Identifying source: name={request.name}, type={request.source_type}")

    try:
        client = _get_supabase_client()
        query = client.table("data_sources").select("*")

        if request.name is None and request.source_type is None:
            # List all sources
            result = query.order("created_at", desc=True).execute()
            return IdentifySourceResult(
                success=True,
                message=f"Found {len(result.data)} sources",
                all_sources=result.data or [],
            )

        exact_match = None
        possible_matches = []

        if request.name:
            # Exact match
            exact_result = query.eq("name", request.name).execute()
            if exact_result.data:
                exact_match = exact_result.data[0]

            # Partial matches (case-insensitive ILIKE)
            partial_result = (
                client.table("data_sources")
                .select("*")
                .ilike("name", f"%{request.name}%")
                .execute()
            )
            possible_matches = [
                r for r in (partial_result.data or [])
                if not exact_match or r.get("id") != exact_match.get("id")
            ]

        if request.source_type and not exact_match:
            type_result = (
                client.table("data_sources")
                .select("*")
                .eq("protocol", request.source_type)
                .execute()
            )
            for r in type_result.data or []:
                if r not in possible_matches:
                    possible_matches.append(r)

        return IdentifySourceResult(
            success=True,
            message=(
                "exact match found"
                if exact_match
                else f"{len(possible_matches)} possible matches"
            ),
            exact_match=exact_match,
            possible_matches=possible_matches,
        )
    except Exception as exc:
        return IdentifySourceResult(
            success=False,
            message=f"Failed to identify source: {exc}",
        )


@activity.defn
async def register_source(request: RegisterSourceRequest) -> RegisterSourceResult:
    """Onboard a new source into the registry.

    Upserts into data_sources table via Supabase, sets status="active".
    """
    activity.logger.info(f"Registering source: {request.name} ({request.protocol})")

    try:
        client = _get_supabase_client()
        result = (
            client.table("data_sources")
            .upsert(
                {
                    "name": request.name,
                    "protocol": request.protocol,
                    "service": request.service,
                    "base_url": request.base_url,
                    "auth_method": request.auth_method,
                    "auth_env_var": request.auth_env_var,
                    "resource_type": request.resource_type,
                    "channel_key": request.channel_key,
                    "config": request.config,
                    "status": "active",
                },
                on_conflict="name",
            )
            .execute()
        )

        source = result.data[0] if result.data else {}
        return RegisterSourceResult(
            success=True,
            message=f"Registered source '{request.name}'",
            source=source,
        )
    except Exception as exc:
        return RegisterSourceResult(
            success=False,
            message=f"Failed to register source: {exc}",
        )


# ---------------------------------------------------------------------------
# Deprecated aliases — kept so IngestWorkflow and other callers don't break.
# Remove when DATA_MGR is wired to the new business verbs.
# ---------------------------------------------------------------------------


@activity.defn
async def connect_source(config: SourceConfig) -> ConnectionResult:
    """Deprecated: use verify_source instead."""
    return await verify_source(config)


@activity.defn
async def fetch_source_data(request: FetchRequest) -> FetchResult:
    """Deprecated: use harvest_records instead."""
    return await harvest_records(request)


@activity.defn
async def test_connection(config: SourceConfig) -> ConnectionResult:
    """Deprecated: use probe_source instead."""
    return await probe_source(config)


@activity.defn
async def get_source_schema(request: FetchRequest) -> SourceSchema:
    """Deprecated: use discover_schema instead."""
    return await discover_schema(request)
