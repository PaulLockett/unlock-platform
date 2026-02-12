"""Unipile connector — unified API for LinkedIn, Instagram, and Gmail.

Unipile provides a single API that proxies to multiple social/email platforms.
We use it for:
  - LinkedIn posts + engagement analytics (likes, comments, impressions)
  - Instagram posts + engagement analytics (likes, comments, reach)
  - Gmail emails for tracking outreach and responses

Auth: Bearer token via Authorization header.
Pagination: Cursor-based (response.pagination.cursor + pagination.hasMore).
Base URL: https://{subdomain}.unipile.com:{port}/api/v1/
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


class UnipileConnector(BaseConnector):
    """Connector for the Unipile unified social/email API."""

    def _default_base_url(self) -> str:
        return "https://api1.unipile.com:13337/api/v1/"

    def _auth_headers(self, credential: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {credential}"}

    def _parse_config(self) -> dict[str, Any]:
        """Parse connector-specific config (account_id, provider, etc.)."""
        if self.config.config_json:
            return json.loads(self.config.config_json)
        return {}

    async def _check_connection(self, client: httpx.AsyncClient) -> ConnectionResult:
        """Verify credentials by fetching the account list."""
        response = await self._request_with_retry(client, "GET", "accounts")
        data = response.json()
        account_count = len(data.get("items", data if isinstance(data, list) else []))
        return ConnectionResult(
            success=True,
            message=f"Connected to Unipile — {account_count} accounts available",
            source_id=self.config.source_id,
            source_type=self.config.source_type,
            data={"account_count": account_count},
        )

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
        cursor: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch one page of posts or emails."""
        extra = self._parse_config()
        account_id = extra.get("account_id", "")

        if request.resource_type == "emails":
            return await self._fetch_emails_page(client, request, cursor, account_id)
        return await self._fetch_posts_page(client, request, cursor, account_id)

    async def _fetch_posts_page(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
        cursor: str | None,
        account_id: str,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch one page of LinkedIn or Instagram posts."""
        params: dict[str, Any] = {"limit": 100}
        if cursor:
            params["cursor"] = cursor
        if request.since:
            params["after"] = request.since.isoformat()

        url = f"users/{account_id}/posts" if account_id else "posts"
        response = await self._request_with_retry(client, "GET", url, params=params)
        data = response.json()

        items = data.get("items", [])
        records = [self._normalize_post(item) for item in items]

        pagination = data.get("pagination", {})
        next_cursor = pagination.get("cursor") if pagination.get("has_more") else None

        return records, next_cursor

    async def _fetch_emails_page(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
        cursor: str | None,
        account_id: str,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch one page of Gmail emails."""
        params: dict[str, Any] = {"limit": 100}
        if cursor:
            params["cursor"] = cursor
        if request.since:
            params["after"] = request.since.isoformat()
        if account_id:
            params["account_id"] = account_id

        response = await self._request_with_retry(client, "GET", "emails", params=params)
        data = response.json()

        items = data.get("items", [])
        records = [self._normalize_email(item) for item in items]

        pagination = data.get("pagination", {})
        next_cursor = pagination.get("cursor") if pagination.get("has_more") else None

        return records, next_cursor

    async def _discover_schema(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
    ) -> dict[str, str]:
        """Discover schema by fetching a small sample and inspecting fields."""
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
    def _normalize_post(item: dict[str, Any]) -> dict[str, Any]:
        """Normalize a Unipile post response to our model shape."""
        return {
            "id": item.get("id", ""),
            "provider": item.get("provider", ""),
            "account_id": item.get("account_id", ""),
            "text": item.get("text", ""),
            "created_at": item.get("created_at"),
            "url": item.get("url", ""),
            "likes": item.get("likes", 0),
            "comments": item.get("comments", 0),
            "shares": item.get("shares", 0),
            "impressions": item.get("impressions", 0),
            "reach": item.get("reach", 0),
            "attachments": item.get("attachments", []),
        }

    @staticmethod
    def _normalize_email(item: dict[str, Any]) -> dict[str, Any]:
        """Normalize a Unipile email response to our model shape."""
        return {
            "id": item.get("id", ""),
            "account_id": item.get("account_id", ""),
            "subject": item.get("subject", ""),
            "from_address": item.get("from", {}).get("address", "")
            if isinstance(item.get("from"), dict)
            else item.get("from", ""),
            "to_addresses": [
                r.get("address", "") if isinstance(r, dict) else r
                for r in item.get("to", [])
            ],
            "cc_addresses": [
                r.get("address", "") if isinstance(r, dict) else r
                for r in item.get("cc", [])
            ],
            "date": item.get("date"),
            "body_plain": item.get("body", {}).get("plain", "")
            if isinstance(item.get("body"), dict)
            else "",
            "body_html": item.get("body", {}).get("html", "")
            if isinstance(item.get("body"), dict)
            else "",
            "is_read": item.get("is_read", False),
            "folder": item.get("folder", ""),
            "attachments": item.get("attachments", []),
        }
