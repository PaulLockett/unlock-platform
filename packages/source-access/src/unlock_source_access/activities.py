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

from temporalio import activity
from unlock_shared.source_models import (
    ConnectionResult,
    FetchRequest,
    FetchResult,
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
