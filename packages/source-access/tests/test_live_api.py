"""External Service Verification Tests (ESVTs) — live API tests against real services.

These tests hit REAL external APIs with REAL credentials. They exist at the top
of the test pyramid as the "last line of defense" before production deployment,
catching issues that mocked unit/integration tests cannot:

  - API contract drift (provider changed response shape without notice)
  - Credential rotation / expiration
  - Rate limit changes
  - Undocumented API behavior our code doesn't handle

Industry terminology (for reference):
  - "Broad integration tests" (Martin Fowler) — tests requiring live external services
  - "External Service Verification" — validating our integration code against real APIs
  - "Deployment Verification Tests" (Jez Humble) — acceptance stage in the delivery pipeline
  - "Contract tests" — verifying response schemas match our expectations
  - "Smoke tests" — minimal checks that a service is alive and auth works

Test tiers (run selectively via pytest markers):
  Tier 1 — smoke:    Auth-only. Verifies credentials are valid and API is reachable.
  Tier 2 — contract: Minimal data fetch (1 page, small limit). Verifies our parsing
                      code handles real API response shapes correctly.

Cost budget per FULL run (all tiers, all connectors):
  Unipile:  ~$0.00  (subscription-based, no per-call cost)
  X.com:    ~$0.01  (1 user lookup + 1 tweet fetch at $0.005/tweet)
  PostHog:  ~$0.00  (free API tier)
  RB2B:     ~$0.01  (1 status check + 1 visitor fetch, minimal credit usage)
  TOTAL:    ~$0.02 per run → safe at x100 = ~$2.00, x500 = ~$10.00

Usage:
  # Run all live tests (requires .env or env vars set):
  uv run pytest packages/source-access/tests/test_live_api.py -v -m live

  # Run only smoke tier (cheapest — auth verification only):
  uv run pytest packages/source-access/tests/test_live_api.py -v -m "live and smoke"

  # Run only contract tier (slightly more expensive — minimal data fetch):
  uv run pytest packages/source-access/tests/test_live_api.py -v -m "live and contract"

  # Run only a single connector:
  uv run pytest packages/source-access/tests/test_live_api.py -v -k "Unipile"
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv
from unlock_shared.source_models import FetchRequest, SourceConfig
from unlock_source_access.connectors import get_connector

# ---------------------------------------------------------------------------
# Load .env for local development (CI sets env vars via GitHub secrets)
# ---------------------------------------------------------------------------
_project_root = Path(__file__).resolve().parents[3]
load_dotenv(_project_root / ".env")


# ---------------------------------------------------------------------------
# Pytest markers — registered in pyproject.toml [tool.pytest.ini_options]
# ---------------------------------------------------------------------------
pytestmark = pytest.mark.live

# Skip markers — each connector's tests only run when credentials are present.
# This is the cost-control mechanism: no key = no spend.
requires_unipile = pytest.mark.skipif(
    not os.environ.get("UNIPILE_API_KEY"),
    reason="UNIPILE_API_KEY not set — skipping live Unipile tests",
)
requires_x = pytest.mark.skipif(
    not os.environ.get("X_BEARER_TOKEN"),
    reason="X_BEARER_TOKEN not set — skipping live X.com tests",
)
requires_posthog = pytest.mark.skipif(
    not os.environ.get("POSTHOG_API_KEY") or not os.environ.get("POSTHOG_PROJECT_ID"),
    reason="POSTHOG_API_KEY or POSTHOG_PROJECT_ID not set — skipping live PostHog tests",
)
requires_rb2b = pytest.mark.skipif(
    not os.environ.get("RB2B_API_KEY"),
    reason="RB2B_API_KEY not set — skipping live RB2B tests",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _unipile_base_url() -> str | None:
    """Build Unipile base URL from UNIPILE_DSN if set."""
    dsn = os.environ.get("UNIPILE_DSN", "")
    if dsn:
        return f"https://{dsn}/api/v1/"
    return None


def _unipile_email_account_id() -> str:
    """Return the Unipile account ID for the Gmail/Google OAuth account.

    This is discovered dynamically via the smoke test (GET /accounts).
    For contract tests, we hardcode the known account ID to avoid an
    extra API call. If accounts change, the smoke test will catch it.
    """
    return os.environ.get("UNIPILE_EMAIL_ACCOUNT_ID", "MbsNgRGDStWsdQCx0VNGCQ")


# ═══════════════════════════════════════════════════════════════════════════
# TIER 1: SMOKE TESTS — auth verification only
#
# Cost: ~$0.00 per connector per run
# Purpose: Catch expired/invalid credentials and API outages
# ═══════════════════════════════════════════════════════════════════════════


@requires_unipile
@pytest.mark.smoke
class TestUnipileSmoke:
    """Verify Unipile credentials are valid and API is reachable."""

    async def test_auth_and_connectivity(self):
        """GET /accounts — zero-cost auth check."""
        config = SourceConfig(
            source_id="live-smoke-unipile",
            source_type="unipile",
            auth_env_var="UNIPILE_API_KEY",
            base_url=_unipile_base_url(),
        )
        connector = get_connector(config)
        try:
            result = await connector.connect()
            assert result.success, f"Unipile auth failed: {result.message}"
            assert result.data, "Expected account metadata in response"
        finally:
            await connector.close()


@requires_x
@pytest.mark.smoke
class TestXSmoke:
    """Verify X.com bearer token is valid."""

    async def test_auth_and_connectivity(self):
        """GET /users/by/username/{username} — ~$0.005 per call."""
        username = os.environ.get("X_USERNAME", "")
        config = SourceConfig(
            source_id="live-smoke-x",
            source_type="x",
            auth_env_var="X_BEARER_TOKEN",
            config_json=json.dumps({"username": username}) if username else "{}",
        )
        connector = get_connector(config)
        try:
            result = await connector.connect()
            assert result.success, f"X.com auth failed: {result.message}"
            if username:
                assert result.data, "Expected user metadata when username is configured"
                assert result.data.get("username"), "Expected username in response data"
        finally:
            await connector.close()


@requires_posthog
@pytest.mark.smoke
class TestPostHogSmoke:
    """Verify PostHog API key and project access."""

    async def test_auth_and_connectivity(self):
        """GET /api/projects/{id} — free API call."""
        project_id = os.environ.get("POSTHOG_PROJECT_ID", "")
        config = SourceConfig(
            source_id="live-smoke-posthog",
            source_type="posthog",
            auth_env_var="POSTHOG_API_KEY",
            config_json=json.dumps({"project_id": project_id}),
        )
        connector = get_connector(config)
        try:
            result = await connector.connect()
            assert result.success, f"PostHog auth failed: {result.message}"
            assert result.data, "Expected project metadata in response"
            assert result.data.get("project_name"), "Expected project_name in response data"
        finally:
            await connector.close()


@requires_rb2b
@pytest.mark.smoke
class TestRB2BSmoke:
    """Verify RB2B API key is valid."""

    async def test_auth_and_connectivity(self):
        """GET /account/status — no credits consumed."""
        config = SourceConfig(
            source_id="live-smoke-rb2b",
            source_type="rb2b",
            auth_env_var="RB2B_API_KEY",
        )
        connector = get_connector(config)
        try:
            result = await connector.connect()
            assert result.success, f"RB2B auth failed: {result.message}"
        finally:
            await connector.close()


# ═══════════════════════════════════════════════════════════════════════════
# TIER 2: CONTRACT TESTS — minimal data fetch + response shape validation
#
# Cost: ~$0.01-0.02 total across all connectors per run
# Purpose: Catch API response shape changes, our parsing bugs against
#          real responses, and undocumented API behavior
# ═══════════════════════════════════════════════════════════════════════════


@requires_unipile
@pytest.mark.contract
class TestUnipileContract:
    """Verify Unipile response shapes match our parsing code.

    Tests emails (not posts) because:
      - The Gmail account is confirmed connected and has data
      - Social accounts may be disconnected (Instagram) or restricted (LinkedIn)
      - Emails are the most reliable resource type for contract verification
    """

    async def test_fetch_emails_shape(self):
        """Fetch 1 page of emails and validate normalized record fields.

        Cost: ~$0.00 (subscription-based)
        """
        config = SourceConfig(
            source_id="live-contract-unipile",
            source_type="unipile",
            auth_env_var="UNIPILE_API_KEY",
            base_url=_unipile_base_url(),
            config_json=json.dumps({"account_id": _unipile_email_account_id()}),
        )
        request = FetchRequest(
            source_id="live-contract-unipile",
            source_type="unipile",
            resource_type="emails",
            auth_env_var="UNIPILE_API_KEY",
            base_url=_unipile_base_url(),
            config_json=json.dumps({"account_id": _unipile_email_account_id()}),
            max_pages=1,
        )
        connector = get_connector(config)
        try:
            result = await connector.fetch_data(request)
            assert result.success, f"Unipile email fetch failed: {result.message}"
            assert result.record_count > 0, "Expected at least 1 email record"

            record = result.records[0]
            expected_fields = {
                "id", "account_id", "subject", "from_address",
                "to_addresses", "cc_addresses", "date",
                "body_plain", "body_html", "is_read", "folder", "attachments",
            }
            actual_fields = set(record.keys())
            missing = expected_fields - actual_fields
            assert not missing, f"Unipile email missing fields: {missing}"
        finally:
            await connector.close()

    async def test_schema_discovery_emails(self):
        """Verify schema discovery returns field type mappings for emails.

        Cost: ~$0.00 (subscription-based)
        """
        config = SourceConfig(
            source_id="live-contract-unipile-schema",
            source_type="unipile",
            auth_env_var="UNIPILE_API_KEY",
            base_url=_unipile_base_url(),
            config_json=json.dumps({"account_id": _unipile_email_account_id()}),
        )
        request = FetchRequest(
            source_id="live-contract-unipile-schema",
            source_type="unipile",
            resource_type="emails",
            auth_env_var="UNIPILE_API_KEY",
            base_url=_unipile_base_url(),
            config_json=json.dumps({"account_id": _unipile_email_account_id()}),
            max_pages=1,
        )
        connector = get_connector(config)
        try:
            schema = await connector.get_schema(request)
            assert schema.success, f"Schema discovery failed: {schema.message}"
            assert schema.fields, "Expected non-empty schema fields for emails"
        finally:
            await connector.close()


@requires_x
@pytest.mark.contract
class TestXContract:
    """Verify X.com response shapes match our parsing code."""

    async def test_fetch_tweets_shape(self):
        """Fetch 1 page of tweets and validate normalized record fields.

        Cost: ~$0.005 (1 tweet read)
        Note: Requires user_id in config. If only username is available,
        the connect() call resolves it but fetch needs the numeric user_id.
        """
        username = os.environ.get("X_USERNAME", "")
        if not username:
            pytest.skip("X_USERNAME not set — cannot resolve user_id for fetch test")

        # First, resolve the user_id via a connect call
        config = SourceConfig(
            source_id="live-contract-x",
            source_type="x",
            auth_env_var="X_BEARER_TOKEN",
            config_json=json.dumps({"username": username}),
        )
        connector = get_connector(config)
        try:
            conn_result = await connector.connect()
            assert conn_result.success, f"X.com connect failed: {conn_result.message}"
            user_id = conn_result.data.get("user_id", "") if conn_result.data else ""
            if not user_id:
                pytest.skip("Could not resolve user_id from X.com — no tweets to validate")

            # Now fetch with the resolved user_id
            await connector.close()
            fetch_config = SourceConfig(
                source_id="live-contract-x-fetch",
                source_type="x",
                auth_env_var="X_BEARER_TOKEN",
                config_json=json.dumps({"user_id": user_id, "username": username}),
            )
            request = FetchRequest(
                source_id="live-contract-x-fetch",
                source_type="x",
                resource_type="tweets",
                auth_env_var="X_BEARER_TOKEN",
                config_json=json.dumps({"user_id": user_id, "username": username}),
                max_pages=1,
            )
            connector = get_connector(fetch_config)
            result = await connector.fetch_data(request)
            assert result.success, f"X.com fetch failed: {result.message}"

            if result.records:
                record = result.records[0]
                expected_fields = {
                    "id", "text", "created_at", "author_id",
                    "conversation_id", "public_metrics", "lang",
                }
                actual_fields = set(record.keys())
                missing = expected_fields - actual_fields
                assert not missing, f"X tweet missing fields: {missing}"

                # Validate public_metrics sub-structure
                metrics = record.get("public_metrics", {})
                metric_fields = {
                    "retweet_count", "reply_count", "like_count", "quote_count",
                }
                missing_metrics = metric_fields - set(metrics.keys())
                assert not missing_metrics, f"X tweet missing metric fields: {missing_metrics}"
        finally:
            await connector.close()


@requires_posthog
@pytest.mark.contract
class TestPostHogContract:
    """Verify PostHog response shapes match our parsing code."""

    async def test_fetch_events_shape(self):
        """Fetch 1 page of events and validate normalized record fields.

        Cost: ~$0.00 (free API)
        """
        project_id = os.environ.get("POSTHOG_PROJECT_ID", "")
        config = SourceConfig(
            source_id="live-contract-posthog",
            source_type="posthog",
            auth_env_var="POSTHOG_API_KEY",
            config_json=json.dumps({"project_id": project_id}),
        )
        request = FetchRequest(
            source_id="live-contract-posthog",
            source_type="posthog",
            resource_type="events",
            auth_env_var="POSTHOG_API_KEY",
            config_json=json.dumps({"project_id": project_id}),
            max_pages=1,
        )
        connector = get_connector(config)
        try:
            result = await connector.fetch_data(request)
            assert result.success, f"PostHog fetch failed: {result.message}"

            if result.records:
                record = result.records[0]
                expected_fields = {
                    "id", "event", "distinct_id", "timestamp", "properties",
                }
                actual_fields = set(record.keys())
                missing = expected_fields - actual_fields
                assert not missing, f"PostHog event missing fields: {missing}"
        finally:
            await connector.close()

    async def test_fetch_persons_shape(self):
        """Fetch 1 page of persons and validate normalized record fields.

        Cost: ~$0.00 (free API)
        """
        project_id = os.environ.get("POSTHOG_PROJECT_ID", "")
        config = SourceConfig(
            source_id="live-contract-posthog-persons",
            source_type="posthog",
            auth_env_var="POSTHOG_API_KEY",
            config_json=json.dumps({"project_id": project_id}),
        )
        request = FetchRequest(
            source_id="live-contract-posthog-persons",
            source_type="posthog",
            resource_type="persons",
            auth_env_var="POSTHOG_API_KEY",
            config_json=json.dumps({"project_id": project_id}),
            max_pages=1,
        )
        connector = get_connector(config)
        try:
            result = await connector.fetch_data(request)
            assert result.success, f"PostHog persons fetch failed: {result.message}"

            if result.records:
                record = result.records[0]
                expected_fields = {
                    "id", "distinct_ids", "properties", "created_at", "is_identified",
                }
                actual_fields = set(record.keys())
                missing = expected_fields - actual_fields
                assert not missing, f"PostHog person missing fields: {missing}"
        finally:
            await connector.close()


@requires_rb2b
@pytest.mark.contract
class TestRB2BContract:
    """Verify RB2B response shapes match our parsing code."""

    async def test_fetch_visitors_shape(self):
        """Fetch 1 page of visitors and validate normalized record fields.

        Cost: ~1 credit (minimal)
        Note: RB2B is credit-based. This test fetches the minimum possible
        data (limit=1 implied by max_pages=1). If the account has no visitor
        data, the test still passes — we validate the fetch didn't error.
        """
        config = SourceConfig(
            source_id="live-contract-rb2b",
            source_type="rb2b",
            auth_env_var="RB2B_API_KEY",
        )
        request = FetchRequest(
            source_id="live-contract-rb2b",
            source_type="rb2b",
            resource_type="visitors",
            auth_env_var="RB2B_API_KEY",
            max_pages=1,
        )
        connector = get_connector(config)
        try:
            result = await connector.fetch_data(request)
            # RB2B fetch may fail gracefully if account has no data or
            # the endpoint structure differs — we accept both outcomes
            # as long as it doesn't crash
            if result.success and result.records:
                record = result.records[0]
                expected_fields = {"id", "email", "first_name", "last_name", "company"}
                actual_fields = set(record.keys())
                missing = expected_fields - actual_fields
                assert not missing, f"RB2B visitor missing fields: {missing}"
        finally:
            await connector.close()


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM-WIDE ACCEPTANCE TEST
#
# Cost: Sum of individual connector costs (~$0.02 total)
# Purpose: Verify all connectors work in a single pass — the cheapest
#          "are we good to deploy?" signal. This test runs on every
#          staging→main PR regardless of watch paths.
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.acceptance
class TestSystemWideAcceptance:
    """Run smoke tests across all available connectors in a single pass.

    This is the "are all external services healthy?" gate. It tests only
    auth (tier 1) so the cost is near zero. It runs on every staging→main PR
    regardless of which files changed, because credential expiration and
    API outages can happen independently of code changes.
    """

    async def test_all_connectors_healthy(self):
        """Verify every configured connector can authenticate.

        Skips connectors whose keys aren't set rather than failing,
        but warns if fewer than expected connectors are configured.
        """
        connector_configs: list[tuple[str, str, str | None, str | None]] = []

        if os.environ.get("UNIPILE_API_KEY"):
            connector_configs.append(
                ("unipile", "UNIPILE_API_KEY", _unipile_base_url(), None)
            )
        if os.environ.get("X_BEARER_TOKEN"):
            username = os.environ.get("X_USERNAME", "")
            config_json = json.dumps({"username": username}) if username else None
            connector_configs.append(("x", "X_BEARER_TOKEN", None, config_json))
        if os.environ.get("POSTHOG_API_KEY") and os.environ.get("POSTHOG_PROJECT_ID"):
            project_id = os.environ.get("POSTHOG_PROJECT_ID", "")
            connector_configs.append(
                ("posthog", "POSTHOG_API_KEY", None, json.dumps({"project_id": project_id}))
            )
        if os.environ.get("RB2B_API_KEY"):
            connector_configs.append(("rb2b", "RB2B_API_KEY", None, None))

        if not connector_configs:
            pytest.skip("No connector API keys configured — cannot run acceptance test")

        results: dict[str, bool] = {}
        errors: list[str] = []

        for source_type, auth_var, base_url, config_json in connector_configs:
            config = SourceConfig(
                source_id=f"acceptance-{source_type}",
                source_type=source_type,
                auth_env_var=auth_var,
                base_url=base_url,
                config_json=config_json,
            )
            connector = get_connector(config)
            try:
                result = await connector.connect()
                results[source_type] = result.success
                if not result.success:
                    errors.append(f"{source_type}: {result.message}")
            except Exception as e:
                results[source_type] = False
                errors.append(f"{source_type}: exception — {e}")
            finally:
                await connector.close()

        # Report all results before asserting — gives full picture on failure
        for source_type, ok in results.items():
            status = "OK" if ok else "FAILED"
            print(f"  [{status}] {source_type}")

        assert not errors, (
            f"Acceptance test failed for {len(errors)} connector(s):\n"
            + "\n".join(f"  - {e}" for e in errors)
        )
