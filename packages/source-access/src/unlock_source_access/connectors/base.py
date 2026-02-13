"""Base connector — shared behavior for all data source connectors.

The ABC enforces the interface that every connector must implement, while
providing real behavior for cross-cutting concerns:

  - Rate limiting via TokenBucket (per-connector instance)
  - Retry with exponential backoff via tenacity (transient HTTP errors)
  - Pagination loop with Temporal heartbeats
  - Consistent error handling: expected failures → result objects,
    transient failures → propagate for Temporal retry

A new data source = a new subclass + one line in the factory dict.
The pagination loop, retry logic, and rate limiting come for free.
"""

from __future__ import annotations

import contextlib
import os
from abc import ABC, abstractmethod
from typing import Any

import httpx
from temporalio import activity
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from unlock_shared.source_models import (
    ConnectionResult,
    FetchRequest,
    FetchResult,
    SourceConfig,
    SourceSchema,
)

from unlock_source_access.rate_limit import TokenBucket


class BaseConnector(ABC):
    """Abstract base for all external data source connectors.

    Subclasses implement the four abstract methods. The base class handles
    HTTP client lifecycle, rate limiting, retries, and pagination.
    """

    def __init__(self, config: SourceConfig) -> None:
        self.config = config
        self.rate_limiter = TokenBucket(rate=config.rate_limit_per_second)
        self._client: httpx.AsyncClient | None = None
        self.request_count: int = 0

    @property
    def source_type(self) -> str:
        return self.config.source_type

    def _resolve_credential(self) -> str:
        """Read the API credential from the environment variable named in config."""
        env_var = self.config.auth_env_var
        if not env_var:
            raise ValueError(f"No auth_env_var configured for source '{self.config.source_id}'")
        value = os.environ.get(env_var, "")
        if not value:
            raise ValueError(f"Environment variable '{env_var}' is not set or empty")
        return value

    def _get_base_url(self) -> str:
        """Return the base URL, preferring config override over the default."""
        if self.config.base_url:
            return self.config.base_url
        return self._default_base_url()

    @abstractmethod
    def _default_base_url(self) -> str:
        """Default API base URL for this connector type."""

    @abstractmethod
    def _auth_headers(self, credential: str) -> dict[str, str]:
        """Build authentication headers from the resolved credential."""

    @abstractmethod
    async def _check_connection(self, client: httpx.AsyncClient) -> ConnectionResult:
        """Verify connectivity — lightweight call to validate credentials."""

    @abstractmethod
    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
        cursor: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch one page of records. Return (records, next_cursor_or_none)."""

    @abstractmethod
    async def _discover_schema(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
    ) -> dict[str, str]:
        """Discover field names and types from a sample of data."""

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client with auth headers."""
        if self._client is None:
            credential = self._resolve_credential()
            headers = self._auth_headers(credential)
            self._client = httpx.AsyncClient(
                base_url=self._get_base_url(),
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def _request_with_retry(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request with rate limiting and retry on transient errors."""
        await self.rate_limiter.acquire()
        self.request_count += 1
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    async def connect(self) -> ConnectionResult:
        """Verify connectivity and return API metadata."""
        try:
            client = await self._get_client()
            return await self._check_connection(client)
        except Exception as e:
            return ConnectionResult(
                success=False,
                message=f"Connection failed: {e}",
                source_id=self.config.source_id,
                source_type=self.config.source_type,
            )

    async def test_connection(self) -> ConnectionResult:
        """Lightweight credential validation — same as connect()."""
        return await self.connect()

    async def fetch_data(self, request: FetchRequest) -> FetchResult:
        """Fetch all records with auto-pagination and Temporal heartbeats.

        Collects all pages within a single activity invocation. Uses
        activity.heartbeat() to signal liveness during long pagination
        runs, preventing Temporal from timing out the activity.
        """
        all_records: list[dict[str, Any]] = []
        cursor: str | None = None
        pages_fetched = 0

        try:
            client = await self._get_client()

            while pages_fetched < request.max_pages:
                records, next_cursor = await self._fetch_page(client, request, cursor)
                all_records.extend(records)
                pages_fetched += 1

                # Heartbeat is best-effort — fails gracefully in tests where
                # there's no Temporal activity context.
                with contextlib.suppress(Exception):
                    activity.heartbeat(
                        f"Fetched page {pages_fetched}, {len(all_records)} records"
                    )

                if not next_cursor:
                    break
                cursor = next_cursor

            return FetchResult(
                success=True,
                message=f"Fetched {len(all_records)} records in {pages_fetched} pages",
                source_id=request.source_id,
                records=all_records,
                record_count=len(all_records),
                has_more=cursor is not None,
            )
        except Exception as e:
            return FetchResult(
                success=False,
                message=f"Fetch failed: {e}",
                source_id=request.source_id,
                records=all_records,
                record_count=len(all_records),
            )

    async def get_schema(self, request: FetchRequest) -> SourceSchema:
        """Discover source field names and types from a sample."""
        try:
            client = await self._get_client()
            fields = await self._discover_schema(client, request)
            return SourceSchema(
                success=True,
                message=f"Discovered {len(fields)} fields",
                source_id=request.source_id,
                fields=fields,
            )
        except Exception as e:
            return SourceSchema(
                success=False,
                message=f"Schema discovery failed: {e}",
                source_id=request.source_id,
            )
