"""RB2B connector — B2B identity resolution via API and file dumps.

RB2B's API Partner Program provides enrichment endpoints that resolve
identity data across different namespaces:

  Identification (IP → identity):
    - ip_to_hem      — IP address → hashed email (MD5/SHA256) with confidence score
    - ip_to_maid     — IP address → Mobile Advertising IDs (IDFA/AAID)
    - ip_to_company  — IP address → company/business profile

  Enrichment (HEM → profile):
    - hem_to_best_linkedin     — hashed email → best LinkedIn URL
    - hem_to_business_profile  — hashed email → company info
    - hem_to_linkedin          — hashed email → LinkedIn slug
    - hem_to_maid              — hashed email → Mobile Advertising IDs

  Enrichment (LinkedIn → contact):
    - linkedin_to_best_personal_email  — LinkedIn slug → best personal email
    - linkedin_to_hashed_emails        — LinkedIn slug → hashed email variants
    - linkedin_to_mobile_phone         — LinkedIn slug → mobile phone
    - linkedin_to_personal_email       — LinkedIn slug → personal email variants
    - linkedin_to_business_profile     — LinkedIn slug → company info

  Search:
    - linkedin_slug_search  — company domain → LinkedIn slug

  Administrative:
    - credits  — GET remaining credit balance

Credit-based pricing — each enrichment call costs credits.
Auth: API key via Api-Key header.

Two modes:
  1. API enrichment — call enrichment endpoints with specific inputs
  2. File dump consumption — parse CSV/JSON exports from RB2B dashboard
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

# Enrichment endpoints and their required input fields.
# Each endpoint is a POST that takes a JSON body with the specified input field.
ENRICHMENT_ENDPOINTS: dict[str, str] = {
    "ip_to_hem": "ip_address",
    "ip_to_maid": "ip_address",
    "ip_to_company": "ip_address",
    "hem_to_best_linkedin": "email",
    "hem_to_business_profile": "email",
    "hem_to_linkedin": "md5",
    "hem_to_maid": "md5",
    "linkedin_to_best_personal_email": "linkedin_slug",
    "linkedin_to_hashed_emails": "linkedin_slug",
    "linkedin_to_mobile_phone": "linkedin_slug",
    "linkedin_to_personal_email": "linkedin_slug",
    "linkedin_to_business_profile": "linkedin_slug",
    "linkedin_slug_search": "company_domain",
}


class RB2BConnector(BaseConnector):
    """Connector for RB2B identity resolution (API enrichment + file dumps)."""

    def _default_base_url(self) -> str:
        return "https://api.rb2b.com/api/v1/"

    def _auth_headers(self, credential: str) -> dict[str, str]:
        return {"Api-Key": credential}

    def _parse_config(self) -> dict[str, Any]:
        """Parse connector-specific config (file_path, enrichment_type, etc.)."""
        if self.config.config_json:
            return json.loads(self.config.config_json)
        return {}

    async def _check_connection(self, client: httpx.AsyncClient) -> ConnectionResult:
        """Verify API credentials by calling the credits endpoint.

        GET /credits returns the remaining credit balance. This validates
        that the API key is active without consuming any credits.
        """
        response = await self._request_with_retry(client, "GET", "credits")
        data = response.json()
        credits_remaining = data.get("credits_remaining", "unknown")
        return ConnectionResult(
            success=True,
            message=f"Connected to RB2B — {credits_remaining} credits remaining",
            source_id=self.config.source_id,
            source_type=self.config.source_type,
            data={"credits_remaining": credits_remaining},
        )

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
        cursor: str | None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch data via enrichment API or file dump.

        For API mode, resource_type must match an enrichment endpoint name
        (e.g. "ip_to_hem"). The required input comes from config_json.
        Enrichment calls are single-shot (no pagination).
        """
        extra = self._parse_config()
        mode = extra.get("mode", "api")

        if mode == "file":
            return self._read_file_dump(extra), None
        return await self._enrich(client, request, extra)

    async def _enrich(
        self,
        client: httpx.AsyncClient,
        request: FetchRequest,
        extra: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Call an enrichment endpoint and return the results.

        The endpoint is determined by request.resource_type (must be a key
        in ENRICHMENT_ENDPOINTS). The required input field's value comes
        from config_json.
        """
        endpoint = request.resource_type
        if endpoint not in ENRICHMENT_ENDPOINTS:
            raise ValueError(
                f"Unknown RB2B resource_type '{endpoint}'. "
                f"Valid types: {', '.join(sorted(ENRICHMENT_ENDPOINTS))}"
            )

        input_field = ENRICHMENT_ENDPOINTS[endpoint]
        input_value = extra.get(input_field)
        if not input_value:
            raise ValueError(
                f"RB2B {endpoint} requires '{input_field}' in config_json"
            )

        body = {input_field: input_value}

        response = await self._request_with_retry(
            client, "POST", endpoint, json=body
        )
        data = response.json()

        # Enrichment responses use "results" (plural) or "result" (singular)
        results = data.get("results") or data.get("result")
        if results is None:
            return [], None

        # Normalize to a list of records
        if isinstance(results, list):
            records = results
        elif isinstance(results, dict):
            records = [results]
        else:
            records = [{"value": results}]

        return records, None

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
        """Discover schema from a sample enrichment call or file dump."""
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
        """Normalize an RB2B visitor/person record from file dumps."""
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
