"""Source Access activities — Temporal activity functions for external data sources.

These run on the source-access worker (SOURCE_ACCESS_QUEUE). The Data Manager's
workflows dispatch to this queue when they need to interact with external data
sources (APIs, files, scraped content).

Four activities — each is an atomic business verb:

  connect_source    — verify connectivity, return API metadata
  fetch_source_data — fetch records with auto-pagination
  test_connection   — lightweight credential validation
  get_source_schema — discover source field names/types from a sample

Each activity creates a connector via the factory, delegates the work, and
ensures the HTTP client is closed afterward. The connector handles retries,
rate limiting, and pagination internally.
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


@activity.defn
async def connect_source(config: SourceConfig) -> ConnectionResult:
    """Verify connectivity to an external data source and return API metadata.

    Used by IngestWorkflow to validate a source before fetching, and by
    ConfigureWorkflow to verify a newly-added source configuration.
    """
    activity.logger.info(f"Connecting to {config.source_type} source '{config.source_id}'")
    connector = get_connector(config)
    try:
        return await connector.connect()
    finally:
        await connector.close()


@activity.defn
async def fetch_source_data(request: FetchRequest) -> FetchResult:
    """Fetch records from an external data source with auto-pagination.

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
        f"source '{config.source_id}'"
    )
    connector = get_connector(config)
    try:
        return await connector.fetch_data(request)
    finally:
        await connector.close()


@activity.defn
async def test_connection(config: SourceConfig) -> ConnectionResult:
    """Lightweight credential validation for a data source.

    Functionally identical to connect_source but semantically distinct —
    used by ConfigureWorkflow when the user wants a quick "does this work?"
    check without committing to a full connection setup.
    """
    activity.logger.info(f"Testing connection to {config.source_type} source '{config.source_id}'")
    connector = get_connector(config)
    try:
        return await connector.test_connection()
    finally:
        await connector.close()


@activity.defn
async def get_source_schema(request: FetchRequest) -> SourceSchema:
    """Discover field names and types from a sample of source data.

    Used by QueryWorkflow to understand the shape of a source before
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
        f"Discovering schema for {config.source_type} source '{config.source_id}'"
    )
    connector = get_connector(config)
    try:
        return await connector.get_schema(request)
    finally:
        await connector.close()
