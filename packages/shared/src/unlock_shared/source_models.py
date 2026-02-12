"""Source Access boundary models — the contract between Data Manager and Source Access.

These types cross the Temporal activity boundary. Workflows in the Data Manager
create them as arguments; activities in Source Access receive and return them.

Design choices:
  - FetchResult.records is list[dict], not list[SomeModel]. Temporal serializes
    everything to JSON, so we use dicts at the boundary. The typed Pydantic models
    (UnipilePost, XTweet, etc.) live in the source-access package and are available
    for the Transform Engine to import and validate against.
  - SourceConfig.auth_env_var names an environment variable, not the credential
    itself. Railway environment variables serve as our secrets manager — we never
    pass secrets through Temporal's data converter.
"""

from datetime import datetime

from pydantic import BaseModel

from unlock_shared.models import PlatformResult


class SourceConfig(BaseModel):
    """Describes how to connect to an external data source."""

    source_id: str
    source_type: str
    base_url: str | None = None
    auth_env_var: str | None = None
    config_json: str | None = None
    rate_limit_per_second: float = 5.0


class FetchRequest(BaseModel):
    """Parameters for a fetch_source_data activity call."""

    source_id: str
    source_type: str
    resource_type: str = "posts"
    since: datetime | None = None
    max_pages: int = 100
    auth_env_var: str | None = None
    base_url: str | None = None
    config_json: str | None = None
    rate_limit_per_second: float = 5.0


class ConnectionResult(PlatformResult):
    """Returned by connect_source and test_connection."""

    source_id: str = ""
    source_type: str = ""


class FetchResult(PlatformResult):
    """Returned by fetch_source_data — carries raw records as dicts."""

    source_id: str = ""
    records: list[dict] = []  # type: ignore[type-arg]
    record_count: int = 0
    has_more: bool = False


class SourceSchema(PlatformResult):
    """Returned by get_source_schema — field names and their inferred types."""

    source_id: str = ""
    fields: dict[str, str] = {}
