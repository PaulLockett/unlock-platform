"""PostHog connector — product analytics events and user data.

PostHog is our product analytics platform for Unlock Alabama web properties.
We fetch events and person profiles for understanding user behavior.

Auth: Personal API key via Authorization header.
Pagination: Offset-based (response.next URL).
Rate limits: 240/min analytics, 1200/hour.
Base URL: https://us.posthog.com/api/projects/{project_id}/
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from unlock_shared.source_models import (
    ConnectionResult,
    FetchRequest,
)

from unlock_source_access.connectors.base import BaseConnector


class PostHogConnector(BaseConnector):
    """Connector for the PostHog analytics API."""

    def _default_base_url(self) -> str:
        return "https://us.posthog.com/api/"

    def _auth_headers(self, credential: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {credential}"}

    def _parse_config(self) -> dict[str, Any]:
        """Parse connector-specific config (project_id, etc.)."""
        if self.config.config_json:
            return json.loads(self.config.config_json)
        return {}

    def _project_prefix(self) -> str:
        """Build the project-scoped URL prefix."""
        extra = self._parse_config()
        project_id = extra.get("project_id", "")
        if project_id:
            return f"projects/{project_id}/"
        return ""

    async def _check_connection(self, client: httpx.AsyncClient) -> ConnectionResult:
        """Verify credentials by fetching the project info."""
        prefix = self._project_prefix()
        if not prefix:
            return ConnectionResult(
                success=False,
                message="PostHog connector requires 'project_id' in config_json",
                source_id=self.config.source_id,
                source_type=self.config.source_type,
            )

        response = await self._request_with_retry(client, "GET", prefix.rstrip("/"))
        data = response.json()
        project_name = data.get("name", "unknown")
        return ConnectionResult(
            success=True,
            message=f"Connected to PostHog project '{project_name}'",
            source_id=self.config.source_id,
            source_type=self.config.source_type,
            data={"project_name": project_name},
        )

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
        cursor: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch one page of events or persons."""
        prefix = self._project_prefix()

        if request.resource_type == "persons":
            return await self._fetch_persons_page(client, prefix, cursor)
        return await self._fetch_events_page(client, request, prefix, cursor)

    async def _fetch_events_page(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
        prefix: str,
        cursor: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch one page of events."""
        params: dict[str, Any] = {"limit": 100}
        if request.since:
            params["after"] = request.since.isoformat()

        # If we have a full cursor URL, use it directly; otherwise build the URL
        if cursor and cursor.startswith("http"):
            response = await self._request_with_retry(client, "GET", cursor)
        else:
            url = f"{prefix}events/"
            if cursor:
                params["offset"] = cursor
            response = await self._request_with_retry(client, "GET", url, params=params)

        data = response.json()
        results = data.get("results", [])
        records = [self._normalize_event(e) for e in results]

        next_url = data.get("next")
        return records, next_url

    async def _fetch_persons_page(
        self,
        client: httpx.AsyncClient,
        prefix: str,
        cursor: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch one page of person profiles."""
        if cursor and cursor.startswith("http"):
            response = await self._request_with_retry(client, "GET", cursor)
        else:
            params: dict[str, Any] = {"limit": 100}
            if cursor:
                params["offset"] = cursor
            response = await self._request_with_retry(
                client, "GET", f"{prefix}persons/", params=params
            )

        data = response.json()
        results = data.get("results", [])
        records = [self._normalize_person(p) for p in results]

        next_url = data.get("next")
        return records, next_url

    async def _discover_schema(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
    ) -> dict[str, str]:
        """Discover schema from a small sample."""
        sample_request = FetchRequest(
            source_id=request.source_id,
            source_type=request.source_type,
            resource_type=request.resource_type,
            max_pages=1,
            auth_env_var=request.auth_env_var,
            base_url=request.base_url,
            config_json=request.config_json,
        )
        records, _ = await self._fetch_page(client, sample_request, None)
        if not records:
            return {}
        return {k: type(v).__name__ for k, v in records[0].items()}

    @staticmethod
    def _normalize_event(item: dict[str, Any]) -> dict[str, Any]:
        """Normalize a PostHog event to our model shape."""
        return {
            "id": item.get("id", ""),
            "event": item.get("event", ""),
            "distinct_id": item.get("distinct_id", ""),
            "timestamp": item.get("timestamp"),
            "properties": item.get("properties", {}),
            "elements": item.get("elements", []),
        }

    @staticmethod
    def _normalize_person(item: dict[str, Any]) -> dict[str, Any]:
        """Normalize a PostHog person to our model shape."""
        return {
            "id": str(item.get("id", "")),
            "distinct_ids": item.get("distinct_ids", []),
            "properties": item.get("properties", {}),
            "created_at": item.get("created_at"),
            "is_identified": item.get("is_identified", False),
        }
