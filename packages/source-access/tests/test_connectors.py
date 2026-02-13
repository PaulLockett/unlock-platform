"""Parametric connector tests with mocked HTTP.

Each connector is tested through the same patterns:
  1. Connection check — verify credentials and return metadata
  2. Single page fetch — fetch records and parse correctly
  3. Multi-page pagination — follow cursors across pages
  4. Schema discovery — infer field types from sample data
  5. Error handling — graceful failure on HTTP errors

All HTTP calls are mocked via MockTransport — no real API calls.
"""

import json
from pathlib import Path

import httpx
import pytest
from unlock_shared.source_models import FetchRequest, SourceConfig
from unlock_source_access.connectors import get_connector
from unlock_source_access.connectors.base import BaseConnector
from unlock_source_access.connectors.posthog import PostHogConnector
from unlock_source_access.connectors.rb2b import RB2BConnector
from unlock_source_access.connectors.unipile import UnipileConnector
from unlock_source_access.connectors.x import XConnector

from .conftest import MockTransport, load_fixture

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _inject_transport(connector, transport):
    """Inject a mock transport into a connector's HTTP client."""
    connector._client = httpx.AsyncClient(
        transport=transport, base_url=connector._get_base_url()
    )


# ---------------------------------------------------------------------------
# Factory tests
# ---------------------------------------------------------------------------


class TestConnectorFactory:
    def test_get_unipile_connector(self, mock_env, unipile_config):
        connector = get_connector(unipile_config)
        assert isinstance(connector, UnipileConnector)

    def test_get_x_connector(self, mock_env, x_config):
        connector = get_connector(x_config)
        assert isinstance(connector, XConnector)

    def test_get_posthog_connector(self, mock_env, posthog_config):
        connector = get_connector(posthog_config)
        assert isinstance(connector, PostHogConnector)

    def test_get_rb2b_connector(self, mock_env, rb2b_config):
        connector = get_connector(rb2b_config)
        assert isinstance(connector, RB2BConnector)

    def test_unknown_type_raises(self, mock_env):
        config = SourceConfig(source_id="bad", source_type="nonexistent")
        with pytest.raises(ValueError, match="Unknown source_type"):
            get_connector(config)

    @pytest.mark.parametrize("source_type", ["unipile", "x", "posthog", "rb2b"])
    def test_all_connectors_are_base_connector(self, mock_env, source_type):
        config = SourceConfig(
            source_id=f"test-{source_type}",
            source_type=source_type,
            auth_env_var=f"{source_type.upper()}_KEY",
        )
        connector = get_connector(config)
        assert isinstance(connector, BaseConnector)


# ---------------------------------------------------------------------------
# Unipile connector tests
# ---------------------------------------------------------------------------


class TestUnipileConnector:
    async def test_connect_success(self, mock_env, unipile_config):
        transport = MockTransport(
            responses=[
                httpx.Response(200, json={"items": [{"id": "acc-1"}, {"id": "acc-2"}]}),
            ]
        )
        connector = UnipileConnector(unipile_config)
        _inject_transport(connector, transport)

        result = await connector.connect()
        assert result.success
        assert "2 accounts" in result.message
        await connector.close()

    async def test_fetch_posts_single_page(self, mock_env, unipile_config, unipile_fetch_request):
        fixture = load_fixture("unipile_posts.json")
        # Return page 1 with cursor, then page 2 with no cursor (end of data)
        page2 = {
            "items": [{"id": "post-003", "provider": "LINKEDIN", "text": "Page 2"}],
            "cursor": None,
        }
        transport = MockTransport(
            responses=[
                httpx.Response(200, json=fixture),
                httpx.Response(200, json=page2),
            ]
        )
        connector = UnipileConnector(unipile_config)
        _inject_transport(connector, transport)

        # Use max_pages=1 to get just first page
        single_page_request = FetchRequest(
            **{**unipile_fetch_request.model_dump(), "max_pages": 1}
        )
        result = await connector.fetch_data(single_page_request)
        assert result.success
        assert result.record_count == 2
        assert result.records[0]["id"] == "post-001"
        assert result.records[1]["likes"] == 128
        await connector.close()

    async def test_fetch_emails(self, mock_env, unipile_config):
        fixture = load_fixture("unipile_emails.json")
        transport = MockTransport(
            responses=[httpx.Response(200, json=fixture)]
        )
        connector = UnipileConnector(unipile_config)
        _inject_transport(connector, transport)

        request = FetchRequest(
            source_id="test-unipile",
            source_type="unipile",
            resource_type="emails",
            auth_env_var="UNIPILE_API_KEY",
            config_json='{"account_id": "acc-789"}',
        )
        result = await connector.fetch_data(request)
        assert result.success
        assert result.record_count == 1
        assert result.records[0]["subject"] == "Partnership opportunity for Unlock Alabama"
        assert result.records[0]["from_address"] == "partner@example.com"
        assert result.records[0]["body_html"] == "<p>Hi, we'd love to discuss...</p>"
        assert result.records[0]["body_plain"] == "Hi, we'd love to discuss..."
        assert result.records[0]["is_read"] is True
        assert result.records[0]["folder"] == "inbox"
        await connector.close()

    async def test_connect_failure(self, mock_env, unipile_config):
        transport = MockTransport(
            responses=[httpx.Response(401, json={"error": "Unauthorized"})]
        )
        connector = UnipileConnector(unipile_config)
        _inject_transport(connector, transport)

        result = await connector.connect()
        assert not result.success
        assert "Connection failed" in result.message
        await connector.close()


# ---------------------------------------------------------------------------
# X.com connector tests
# ---------------------------------------------------------------------------


class TestXConnector:
    async def test_connect_with_username(self, mock_env, x_config):
        transport = MockTransport(
            responses=[
                httpx.Response(200, json={
                    "data": {"id": "9876543210", "username": "unlockalabama"}
                }),
            ]
        )
        connector = XConnector(x_config)
        _inject_transport(connector, transport)

        result = await connector.connect()
        assert result.success
        assert "@unlockalabama" in result.message
        await connector.close()

    async def test_fetch_tweets(self, mock_env, x_config, x_fetch_request):
        fixture = load_fixture("x_tweets.json")
        # Page 1 has next_token, page 2 does not
        page2 = {"data": [], "meta": {"result_count": 0}}
        transport = MockTransport(
            responses=[
                httpx.Response(200, json=fixture),
                httpx.Response(200, json=page2),
            ]
        )
        connector = XConnector(x_config)
        _inject_transport(connector, transport)

        result = await connector.fetch_data(x_fetch_request)
        assert result.success
        assert result.record_count == 2
        assert result.records[0]["public_metrics"]["like_count"] == 45
        assert result.records[1]["text"].startswith("Check out")
        await connector.close()

    async def test_fetch_requires_user_id(self, mock_env):
        config = SourceConfig(
            source_id="test-x",
            source_type="x",
            auth_env_var="X_BEARER_TOKEN",
            config_json="{}",  # No user_id
        )
        connector = XConnector(config)
        _inject_transport(connector, MockTransport())

        request = FetchRequest(
            source_id="test-x",
            source_type="x",
            auth_env_var="X_BEARER_TOKEN",
            config_json="{}",
        )
        result = await connector.fetch_data(request)
        assert not result.success
        assert "user_id" in result.message
        await connector.close()


# ---------------------------------------------------------------------------
# PostHog connector tests
# ---------------------------------------------------------------------------


class TestPostHogConnector:
    async def test_connect_success(self, mock_env, posthog_config):
        transport = MockTransport(
            responses=[
                httpx.Response(200, json={"name": "Unlock Alabama Analytics"}),
            ]
        )
        connector = PostHogConnector(posthog_config)
        _inject_transport(connector, transport)

        result = await connector.connect()
        assert result.success
        assert "Unlock Alabama Analytics" in result.message
        await connector.close()

    async def test_connect_requires_project_id(self, mock_env):
        config = SourceConfig(
            source_id="test-ph",
            source_type="posthog",
            auth_env_var="POSTHOG_API_KEY",
            config_json="{}",
        )
        connector = PostHogConnector(config)
        _inject_transport(connector, MockTransport())

        result = await connector.connect()
        assert not result.success
        assert "project_id" in result.message
        await connector.close()

    async def test_fetch_events(self, mock_env, posthog_config, posthog_fetch_request):
        fixture = load_fixture("posthog_events.json")
        # Page 2 has no next URL
        page2 = {"results": [], "next": None}
        transport = MockTransport(
            responses=[
                httpx.Response(200, json=fixture),
                httpx.Response(200, json=page2),
            ]
        )
        connector = PostHogConnector(posthog_config)
        _inject_transport(connector, transport)

        result = await connector.fetch_data(posthog_fetch_request)
        assert result.success
        assert result.record_count == 2
        assert result.records[0]["event"] == "$pageview"
        await connector.close()

    async def test_fetch_persons(self, mock_env, posthog_config):
        fixture = load_fixture("posthog_persons.json")
        transport = MockTransport(
            responses=[httpx.Response(200, json=fixture)]
        )
        connector = PostHogConnector(posthog_config)
        _inject_transport(connector, transport)

        request = FetchRequest(
            source_id="test-posthog",
            source_type="posthog",
            resource_type="persons",
            auth_env_var="POSTHOG_API_KEY",
            config_json='{"project_id": "12345"}',
        )
        result = await connector.fetch_data(request)
        assert result.success
        assert result.record_count == 1
        assert result.records[0]["is_identified"] is True
        await connector.close()


# ---------------------------------------------------------------------------
# RB2B connector tests
# ---------------------------------------------------------------------------


class TestRB2BConnector:
    async def test_connect_success(self, mock_env, rb2b_config):
        transport = MockTransport(
            responses=[
                httpx.Response(200, json={"credits_remaining": 500}),
            ]
        )
        connector = RB2BConnector(rb2b_config)
        _inject_transport(connector, transport)

        result = await connector.connect()
        assert result.success
        assert "500 credits" in result.message
        await connector.close()

    async def test_connect_http_error_propagates(self, mock_env, rb2b_config):
        """HTTP errors from account/status must propagate as connection failures.

        RB2B returns 404 when the API key has no activated endpoints, and
        401/403 when auth fails. All of these are real failures — the connector
        must NOT swallow them, otherwise tests falsely pass.
        """
        transport = MockTransport(
            responses=[httpx.Response(404, json={"error": "not found"})]
        )
        connector = RB2BConnector(rb2b_config)
        _inject_transport(connector, transport)

        result = await connector.connect()
        assert not result.success
        assert "Connection failed" in result.message
        await connector.close()

    async def test_connect_401_unauthorized(self, mock_env, rb2b_config):
        """401 Unauthorized must surface as connection failure."""
        transport = MockTransport(
            responses=[httpx.Response(401, json={"error": "unauthorized"})]
        )
        connector = RB2BConnector(rb2b_config)
        _inject_transport(connector, transport)

        result = await connector.connect()
        assert not result.success
        assert "Connection failed" in result.message
        await connector.close()

    async def test_fetch_visitors_api(self, mock_env, rb2b_config, rb2b_fetch_request):
        fixture = load_fixture("rb2b_visitors.json")
        transport = MockTransport(
            responses=[httpx.Response(200, json=fixture)]
        )
        connector = RB2BConnector(rb2b_config)
        _inject_transport(connector, transport)

        result = await connector.fetch_data(rb2b_fetch_request)
        assert result.success
        assert result.record_count == 1
        assert result.records[0]["email"] == "jsmith@techcorp.com"
        assert result.records[0]["company"]["name"] == "TechCorp Alabama"
        await connector.close()

    async def test_fetch_file_dump_csv(self, mock_env):
        csv_path = str(FIXTURES_DIR / "rb2b_dump.csv")
        config = SourceConfig(
            source_id="test-rb2b-file",
            source_type="rb2b",
            auth_env_var="RB2B_API_KEY",
            config_json=json.dumps({"mode": "file", "file_path": csv_path}),
        )
        connector = RB2BConnector(config)
        # File mode doesn't need HTTP, but we still need a client for the base class
        _inject_transport(connector, MockTransport())

        request = FetchRequest(
            source_id="test-rb2b-file",
            source_type="rb2b",
            auth_env_var="RB2B_API_KEY",
            config_json=json.dumps({"mode": "file", "file_path": csv_path}),
        )
        result = await connector.fetch_data(request)
        assert result.success
        assert result.record_count == 2
        assert result.records[0]["first_name"] == "Jane"
        assert result.records[0]["company"]["name"] == "Civic Solutions"
        assert result.records[1]["visit_count"] == 1
        await connector.close()

    async def test_fetch_file_dump_json(self, mock_env, tmp_path):
        """Test JSON file dump parsing."""
        json_data = [
            {
                "id": "json-001",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
                "company": {"name": "TestCo"},
            }
        ]
        json_file = tmp_path / "visitors.json"
        json_file.write_text(json.dumps(json_data))

        config = SourceConfig(
            source_id="test-rb2b-json",
            source_type="rb2b",
            auth_env_var="RB2B_API_KEY",
            config_json=json.dumps({"mode": "file", "file_path": str(json_file)}),
        )
        connector = RB2BConnector(config)
        _inject_transport(connector, MockTransport())

        request = FetchRequest(
            source_id="test-rb2b-json",
            source_type="rb2b",
            auth_env_var="RB2B_API_KEY",
            config_json=json.dumps({"mode": "file", "file_path": str(json_file)}),
        )
        result = await connector.fetch_data(request)
        assert result.success
        assert result.record_count == 1
        assert result.records[0]["email"] == "test@example.com"
        await connector.close()


# ---------------------------------------------------------------------------
# Credential resolution tests
# ---------------------------------------------------------------------------


class TestCredentialResolution:
    @pytest.mark.parametrize("source_type", ["unipile", "x", "posthog", "rb2b"])
    async def test_missing_env_var_fails_gracefully(self, source_type):
        """When the env var is missing, connect returns success=False."""
        config = SourceConfig(
            source_id=f"test-{source_type}",
            source_type=source_type,
            auth_env_var=f"NONEXISTENT_{source_type.upper()}_KEY",
        )
        connector = get_connector(config)
        result = await connector.connect()
        assert not result.success
        assert "not set" in result.message or "Connection failed" in result.message
        await connector.close()

    async def test_no_auth_env_var_configured(self, mock_env):
        config = SourceConfig(
            source_id="test",
            source_type="unipile",
            auth_env_var=None,
        )
        connector = get_connector(config)
        result = await connector.connect()
        assert not result.success
        await connector.close()


# ---------------------------------------------------------------------------
# Schema discovery tests
# ---------------------------------------------------------------------------


class TestSchemaDiscovery:
    async def test_unipile_schema(self, mock_env, unipile_config):
        fixture = load_fixture("unipile_posts.json")
        transport = MockTransport(
            responses=[httpx.Response(200, json=fixture)]
        )
        connector = UnipileConnector(unipile_config)
        _inject_transport(connector, transport)

        request = FetchRequest(
            source_id="test-unipile",
            source_type="unipile",
            auth_env_var="UNIPILE_API_KEY",
            config_json='{"account_id": "acc-123"}',
        )
        result = await connector.get_schema(request)
        assert result.success
        assert "id" in result.fields
        assert "likes" in result.fields
        await connector.close()

    async def test_x_schema(self, mock_env, x_config):
        fixture = load_fixture("x_tweets.json")
        transport = MockTransport(
            responses=[httpx.Response(200, json=fixture)]
        )
        connector = XConnector(x_config)
        _inject_transport(connector, transport)

        request = FetchRequest(
            source_id="test-x",
            source_type="x",
            auth_env_var="X_BEARER_TOKEN",
            config_json='{"user_id": "9876543210"}',
        )
        result = await connector.get_schema(request)
        assert result.success
        assert "id" in result.fields
        assert "public_metrics" in result.fields
        await connector.close()
