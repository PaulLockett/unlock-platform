"""X.com (Twitter) connector — API v2 for owned account posts and metrics.

We read our own account's tweets and their public engagement metrics.
The X API v2 uses a flat data + includes architecture.

Auth: OAuth 2.0 Bearer token (app-only).
Pagination: pagination_token in meta.next_token.
Pricing: Pay-per-use ($0.005/read tweet, $0.01/profile). Connector logs usage.
Base URL: https://api.x.com/2/
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from unlock_shared.source_models import (
    ConnectionResult,
    FetchRequest,
)

from unlock_source_access.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class XConnector(BaseConnector):
    """Connector for the X.com (Twitter) API v2."""

    def _default_base_url(self) -> str:
        return "https://api.x.com/2/"

    def _auth_headers(self, credential: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {credential}"}

    def _parse_config(self) -> dict[str, Any]:
        """Parse connector-specific config (user_id, username, etc.)."""
        if self.config.config_json:
            return json.loads(self.config.config_json)
        return {}

    async def _check_connection(self, client: httpx.AsyncClient) -> ConnectionResult:
        """Verify credentials by looking up the authenticated user or a configured one."""
        extra = self._parse_config()
        username = extra.get("username", "")

        if username:
            response = await self._request_with_retry(
                client,
                "GET",
                f"users/by/username/{username}",
            )
            data = response.json()
            user = data.get("data", {})
            return ConnectionResult(
                success=True,
                message=f"Connected to X — user @{user.get('username', username)}",
                source_id=self.config.source_id,
                source_type=self.config.source_type,
                data={"user_id": user.get("id", ""), "username": user.get("username", "")},
            )

        # Without a username, just verify the token works with /users/me (if available)
        # For app-only tokens, this won't work — fall back to a basic check
        return ConnectionResult(
            success=True,
            message="X API token provided (no username configured for lookup)",
            source_id=self.config.source_id,
            source_type=self.config.source_type,
        )

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
        cursor: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch one page of tweets from the configured user."""
        extra = self._parse_config()
        user_id = extra.get("user_id", "")
        if not user_id:
            raise ValueError("X connector requires 'user_id' in config_json")

        params: dict[str, Any] = {
            "max_results": 100,
            "tweet.fields": "created_at,author_id,conversation_id,public_metrics,lang,"
            "edit_history_tweet_ids",
        }
        if cursor:
            params["pagination_token"] = cursor
        if request.since:
            params["start_time"] = request.since.strftime("%Y-%m-%dT%H:%M:%SZ")

        response = await self._request_with_retry(
            client,
            "GET",
            f"users/{user_id}/tweets",
            params=params,
        )
        data = response.json()

        tweets = data.get("data", [])
        records = [self._normalize_tweet(t) for t in tweets]

        # Log cost for awareness (pay-per-use model)
        if records:
            logger.info(f"X API: fetched {len(records)} tweets (~${len(records) * 0.005:.3f})")

        meta = data.get("meta", {})
        next_token = meta.get("next_token")

        return records, next_token

    async def _discover_schema(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
    ) -> dict[str, str]:
        """Discover schema from a small sample of tweets."""
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
    def _normalize_tweet(item: dict[str, Any]) -> dict[str, Any]:
        """Normalize an X API v2 tweet to our model shape."""
        metrics = item.get("public_metrics", {})
        return {
            "id": item.get("id", ""),
            "text": item.get("text", ""),
            "created_at": item.get("created_at"),
            "author_id": item.get("author_id", ""),
            "conversation_id": item.get("conversation_id", ""),
            "public_metrics": {
                "retweet_count": metrics.get("retweet_count", 0),
                "reply_count": metrics.get("reply_count", 0),
                "like_count": metrics.get("like_count", 0),
                "quote_count": metrics.get("quote_count", 0),
                "bookmark_count": metrics.get("bookmark_count", 0),
                "impression_count": metrics.get("impression_count", 0),
            },
            "lang": item.get("lang", ""),
            "edit_history_tweet_ids": item.get("edit_history_tweet_ids", []),
        }
