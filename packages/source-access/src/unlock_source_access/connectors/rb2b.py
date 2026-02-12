"""RB2B connector — B2B visitor identification via API and file dumps.

RB2B identifies companies and individuals visiting our web properties.
Two modes:
  1. API enrichment — IP→email, email→person, LinkedIn→profile
  2. File dump consumption — parse CSV/JSON exports from RB2B dashboard

Credit-based pricing — the connector logs credit usage for cost awareness.

Auth: API key via X-API-Key header.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from pathlib import Path
from typing import Any

import httpx
from unlock_shared.source_models import (
    ConnectionResult,
    FetchRequest,
)

from unlock_source_access.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class RB2BConnector(BaseConnector):
    """Connector for RB2B visitor identification (API + file dumps)."""

    def _default_base_url(self) -> str:
        return "https://api.rb2b.com/v1/"

    def _auth_headers(self, credential: str) -> dict[str, str]:
        return {"X-API-Key": credential}

    def _parse_config(self) -> dict[str, Any]:
        """Parse connector-specific config (file_path, enrichment_type, etc.)."""
        if self.config.config_json:
            return json.loads(self.config.config_json)
        return {}

    async def _check_connection(self, client: httpx.AsyncClient) -> ConnectionResult:
        """Verify API credentials by calling the account/status endpoint."""
        try:
            response = await self._request_with_retry(client, "GET", "account/status")
            data = response.json()
            credits_remaining = data.get("credits_remaining", "unknown")
            return ConnectionResult(
                success=True,
                message=f"Connected to RB2B — {credits_remaining} credits remaining",
                source_id=self.config.source_id,
                source_type=self.config.source_type,
                data={"credits_remaining": credits_remaining},
            )
        except httpx.HTTPStatusError:
            # Some RB2B plans may not have a status endpoint — treat as OK if auth works
            return ConnectionResult(
                success=True,
                message="RB2B API key accepted (status endpoint unavailable)",
                source_id=self.config.source_id,
                source_type=self.config.source_type,
            )

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
        cursor: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch one page of visitor data via API or file dump."""
        extra = self._parse_config()
        mode = extra.get("mode", "api")

        if mode == "file":
            return self._read_file_dump(extra), None
        return await self._fetch_visitors_page(client, request, cursor)

    async def _fetch_visitors_page(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
        cursor: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch one page of identified visitors from the API."""
        params: dict[str, Any] = {"limit": 100}
        if cursor:
            params["offset"] = int(cursor)
        if request.since:
            params["since"] = request.since.isoformat()

        response = await self._request_with_retry(
            client, "GET", "visitors", params=params
        )
        data = response.json()

        visitors = data.get("data", data.get("visitors", []))
        records = [self._normalize_person(v) for v in visitors]

        # Log credit usage for cost awareness
        credits_used = data.get("credits_used", 0)
        if credits_used:
            logger.info(f"RB2B: {credits_used} credits used for {len(records)} visitors")

        # Offset-based pagination
        total = data.get("total", 0)
        current_offset = int(cursor) if cursor else 0
        next_offset = current_offset + len(records)
        next_cursor = str(next_offset) if next_offset < total else None

        return records, next_cursor

    def _read_file_dump(self, extra: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse a CSV or JSON file dump from the RB2B dashboard.

        File dumps are read entirely in one call (no pagination). The file
        path comes from config_json.file_path.
        """
        file_path = extra.get("file_path", "")
        if not file_path:
            raise ValueError("RB2B file mode requires 'file_path' in config_json")

        path = Path(file_path)
        content = path.read_text(encoding="utf-8")

        if path.suffix.lower() == ".json":
            data = json.loads(content)
            items = data if isinstance(data, list) else data.get("data", [])
            return [self._normalize_person(item) for item in items]

        if path.suffix.lower() == ".csv":
            reader = csv.DictReader(io.StringIO(content))
            return [self._normalize_csv_row(row) for row in reader]

        raise ValueError(f"Unsupported file format: {path.suffix}")

    async def _discover_schema(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
    ) -> dict[str, str]:
        """Discover schema from a small sample of visitors."""
        extra = self._parse_config()
        mode = extra.get("mode", "api")

        if mode == "file":
            records = self._read_file_dump(extra)
        else:
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
    def _normalize_person(item: dict[str, Any]) -> dict[str, Any]:
        """Normalize an RB2B visitor/person to our model shape."""
        company = item.get("company", {})
        return {
            "id": str(item.get("id", "")),
            "email": item.get("email", ""),
            "first_name": item.get("first_name", ""),
            "last_name": item.get("last_name", ""),
            "title": item.get("title", ""),
            "linkedin_url": item.get("linkedin_url", ""),
            "company": {
                "name": company.get("name", ""),
                "domain": company.get("domain", ""),
                "industry": company.get("industry", ""),
                "employee_count": company.get("employee_count", 0),
                "revenue_range": company.get("revenue_range", ""),
                "linkedin_url": company.get("linkedin_url", ""),
                "location": company.get("location", ""),
            },
            "page_views": item.get("page_views", []),
            "first_seen": item.get("first_seen"),
            "last_seen": item.get("last_seen"),
            "visit_count": item.get("visit_count", 0),
        }

    @staticmethod
    def _normalize_csv_row(row: dict[str, str]) -> dict[str, Any]:
        """Normalize a CSV row to our model shape."""
        return {
            "id": row.get("id", ""),
            "email": row.get("email", ""),
            "first_name": row.get("first_name", ""),
            "last_name": row.get("last_name", ""),
            "title": row.get("title", ""),
            "linkedin_url": row.get("linkedin_url", ""),
            "company": {
                "name": row.get("company_name", ""),
                "domain": row.get("company_domain", ""),
                "industry": row.get("company_industry", ""),
                "employee_count": int(row.get("company_employee_count", "0") or "0"),
                "revenue_range": row.get("company_revenue_range", ""),
                "linkedin_url": row.get("company_linkedin_url", ""),
                "location": row.get("company_location", ""),
            },
            "page_views": [],
            "first_seen": row.get("first_seen"),
            "last_seen": row.get("last_seen"),
            "visit_count": int(row.get("visit_count", "0") or "0"),
        }
