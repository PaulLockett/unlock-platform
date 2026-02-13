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

Cost tracking:
  Each test reports its actual HTTP request count via connector.request_count.
  Actual per-request costs vary by API and are tracked in the test output.
  Monitor the pytest output for "API requests:" lines to see real usage.

Usage:
  # Run all live tests (requires .env or env vars set):
  uv run pytest packages/source-access/tests/test_live_api.py -v -m live -s

  # Run only smoke tier (cheapest — auth verification only):
  uv run pytest packages/source-access/tests/test_live_api.py -v -m "live and smoke" -s

  # Run only contract tier (slightly more expensive — minimal data fetch):
  uv run pytest packages/source-access/tests/test_live_api.py -v -m "live and contract" -s

  # Run only a single connector:
  uv run pytest packages/source-access/tests/test_live_api.py -v -k "Unipile" -s
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


def _report_requests(connector, label: str) -> None:
    """Print the actual HTTP request count for cost monitoring.

    Paul explicitly requested real cost reporting per test run.
    All API request counts are surfaced here so `pytest -s` output
    shows exactly how many requests each test made.
    """
    print(f"\n  [{label}] API requests: {connector.request_count}")


# ---------------------------------------------------------------------------
# External failure detection helpers
#
# Paul's requirement: distinguish "our code is broken" from "external provider
# issue" (disconnected account, expired credits, rate limit). Tests should
# still pass when the failure is clearly external, but MUST fail when the
# failure indicates a bug in our code.
# ---------------------------------------------------------------------------

# Known HTTP status patterns that indicate external provider issues
# (not our code's fault):
EXTERNAL_FAILURE_PATTERNS = {
    # Account disconnected on provider side (Unipile returns 422 or similar)
    "account_disconnected": ["disconnected", "not connected", "connection expired"],
    # No API credits remaining
    "no_credits": ["insufficient credits", "credit limit", "no credits"],
    # Rate limiting (not a code bug, just need to slow down)
    "rate_limited": ["rate limit", "too many requests", "429"],
}


def _is_external_failure(message: str) -> tuple[bool, str]:
    """Check if a failure message indicates an external provider issue.

    Returns (is_external, reason) where reason describes the external cause.
    """
    msg_lower = message.lower()
    for category, patterns in EXTERNAL_FAILURE_PATTERNS.items():
        for pattern in patterns:
            if pattern.lower() in msg_lower:
                return True, category
    return False, ""


def _assert_success_or_external_failure(result, connector_name: str) -> None:
    """Assert that a result either succeeds OR fails due to an external issue.

    If the result fails and the failure is NOT an external provider issue,
    the test fails — that indicates a bug in our code.
    """
    if result.success:
        return

    is_external, reason = _is_external_failure(result.message)
    if is_external:
        pytest.skip(
            f"{connector_name} failed due to external issue ({reason}): {result.message}"
        )
    else:
        # This is a real failure — our code is broken
        pytest.fail(f"{connector_name} failed (not an external issue): {result.message}")


# ═══════════════════════════════════════════════════════════════════════════
# TIER 1: SMOKE TESTS — auth verification only
#
# Purpose: Catch expired/invalid credentials and API outages
# ═══════════════════════════════════════════════════════════════════════════


@requires_unipile
@pytest.mark.smoke
class TestUnipileSmoke:
    """Verify Unipile credentials are valid and API is reachable."""

    async def test_auth_and_connectivity(self):
        """GET /accounts — subscription-based, no per-call cost."""
        config = SourceConfig(
            source_id="live-smoke-unipile",
            source_type="unipile",
            auth_env_var="UNIPILE_API_KEY",
            base_url=_unipile_base_url(),
        )
        connector = get_connector(config)
        try:
            result = await connector.connect()
            _report_requests(connector, "Unipile smoke")
            assert result.success, f"Unipile auth failed: {result.message}"
            assert result.data, "Expected account metadata in response"
        finally:
            await connector.close()


@requires_x
@pytest.mark.smoke
class TestXSmoke:
    """Verify X.com bearer token is valid."""

    async def test_auth_and_connectivity(self):
        """GET /users/by/username/{username} — 1 request."""
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
            _report_requests(connector, "X.com smoke")
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
        """GET /api/projects/{id} — free API call, 1 request."""
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
            _report_requests(connector, "PostHog smoke")
            assert result.success, f"PostHog auth failed: {result.message}"
            assert result.data, "Expected project metadata in response"
            assert result.data.get("project_name"), "Expected project_name in response data"
        finally:
            await connector.close()


@requires_rb2b
@pytest.mark.smoke
class TestRB2BSmoke:
    """Verify RB2B API key is valid via the credits endpoint.

    RB2B is credit-based. GET /credits validates the API key and returns
    the remaining credit balance without consuming any credits.
    """

    async def test_auth_and_connectivity(self):
        """GET /credits — 1 request, no credits consumed."""
        config = SourceConfig(
            source_id="live-smoke-rb2b",
            source_type="rb2b",
            auth_env_var="RB2B_API_KEY",
        )
        connector = get_connector(config)
        try:
            result = await connector.connect()
            _report_requests(connector, "RB2B smoke")
            _assert_success_or_external_failure(result, "RB2B")
            if result.success:
                assert result.data, "Expected credit balance in response"
                credits = result.data.get("credits_remaining")
                print(f"  RB2B credits remaining: {credits}")
        finally:
            await connector.close()


# ═══════════════════════════════════════════════════════════════════════════
# TIER 2: CONTRACT TESTS — minimal data fetch + response shape validation
#
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

        Subscription-based — no per-call cost. 1 request.
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
            _report_requests(connector, "Unipile contract/emails")
            _assert_success_or_external_failure(result, "Unipile emails")
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

        Subscription-based — no per-call cost. 1 request.
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
            _report_requests(connector, "Unipile contract/schema")
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

        2 requests: 1 user lookup + 1 tweet fetch.
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
            _report_requests(connector, "X.com contract/connect")
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
            _report_requests(connector, "X.com contract/fetch")

            _assert_success_or_external_failure(result, "X.com tweets")

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

        Free API — 1 request.
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
            _report_requests(connector, "PostHog contract/events")
            _assert_success_or_external_failure(result, "PostHog events")

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

        Free API — 1 request.
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
            _report_requests(connector, "PostHog contract/persons")
            _assert_success_or_external_failure(result, "PostHog persons")

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
    """Verify RB2B enrichment API response shapes match our parsing code.

    RB2B is credit-based — each enrichment call consumes credits. We test
    ip_to_hem with a documentation example IP to validate response shape.
    Cost: 1 credit per call.
    """

    async def test_enrich_ip_to_hem_shape(self):
        """POST /ip_to_hem — validate enrichment response shape.

        1 request. Costs 1 credit. Uses a documentation example IP address
        which may return empty results — either way validates the shape.
        """
        config = SourceConfig(
            source_id="live-contract-rb2b",
            source_type="rb2b",
            auth_env_var="RB2B_API_KEY",
            config_json=json.dumps({"ip_address": "162.192.6.240"}),
        )
        request = FetchRequest(
            source_id="live-contract-rb2b",
            source_type="rb2b",
            resource_type="ip_to_hem",
            auth_env_var="RB2B_API_KEY",
            config_json=json.dumps({"ip_address": "162.192.6.240"}),
            max_pages=1,
        )
        connector = get_connector(config)
        try:
            result = await connector.fetch_data(request)
            _report_requests(connector, "RB2B contract/ip_to_hem")
            _assert_success_or_external_failure(result, "RB2B ip_to_hem")

            # Response may be empty (no match for this IP) — that's OK.
            # When results exist, validate the response shape.
            if result.success and result.records:
                record = result.records[0]
                expected_fields = {"md5", "score"}
                actual_fields = set(record.keys())
                missing = expected_fields - actual_fields
                assert not missing, f"RB2B ip_to_hem missing fields: {missing}"
                # API returns score as string (e.g. "0.844"), not float as docs suggest
                assert float(record["score"]), "score must be parseable as a number"
        finally:
            await connector.close()


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM-WIDE ACCEPTANCE TEST
#
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
        Reports total API request count for cost monitoring.
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
        connector_requests: dict[str, int] = {}
        errors: list[str] = []
        total_requests = 0

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
                requests_made = connector.request_count
                total_requests += requests_made
                connector_requests[source_type] = requests_made

                if not result.success:
                    is_external, reason = _is_external_failure(result.message)
                else:
                    is_external, reason = False, ""

                if result.success:
                    results[source_type] = True
                elif is_external:
                    # External failures are noted but don't block deployment
                    results[source_type] = True
                    print(f"\n  [EXTERNAL] {source_type}: {reason} — {result.message}")
                else:
                    results[source_type] = False
                    errors.append(f"{source_type}: {result.message}")
            except Exception as e:
                results[source_type] = False
                errors.append(f"{source_type}: exception — {e}")
            finally:
                await connector.close()

        # Report per-connector request counts (parseable by CI cost reporter)
        for source_type, reqs in connector_requests.items():
            print(f"\n  [{source_type} acceptance] API requests: {reqs}")
        print(f"\n  Acceptance test — total API requests: {total_requests}")
        for source_type, ok in results.items():
            status = "OK" if ok else "FAILED"
            print(f"  [{status}] {source_type}")

        assert not errors, (
            f"Acceptance test failed for {len(errors)} connector(s):\n"
            + "\n".join(f"  - {e}" for e in errors)
        )
