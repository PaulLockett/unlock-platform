"""Integration tests — run against real APIs with real credentials.

These tests are SKIPPED unless the corresponding API key environment variable
is set. They're designed to run in the staging environment where Paul has
added real API keys.

Run with: uv run pytest packages/source-access/tests/test_integration.py -v
"""

import os

import pytest
from unlock_shared.source_models import SourceConfig
from unlock_source_access.connectors import get_connector

# Skip markers — tests only run when credentials are present
requires_unipile = pytest.mark.skipif(
    not os.environ.get("UNIPILE_API_KEY"),
    reason="UNIPILE_API_KEY not set",
)
requires_x = pytest.mark.skipif(
    not os.environ.get("X_BEARER_TOKEN"),
    reason="X_BEARER_TOKEN not set",
)
requires_posthog = pytest.mark.skipif(
    not os.environ.get("POSTHOG_API_KEY"),
    reason="POSTHOG_API_KEY not set",
)
requires_rb2b = pytest.mark.skipif(
    not os.environ.get("RB2B_API_KEY"),
    reason="RB2B_API_KEY not set",
)


@requires_unipile
class TestUnipileIntegration:
    async def test_connect(self):
        config = SourceConfig(
            source_id="integration-unipile",
            source_type="unipile",
            auth_env_var="UNIPILE_API_KEY",
        )
        connector = get_connector(config)
        try:
            result = await connector.connect()
            assert result.success, f"Connection failed: {result.message}"
        finally:
            await connector.close()


@requires_x
class TestXIntegration:
    async def test_connect(self):
        username = os.environ.get("X_USERNAME", "")
        config = SourceConfig(
            source_id="integration-x",
            source_type="x",
            auth_env_var="X_BEARER_TOKEN",
            config_json=f'{{"username": "{username}"}}' if username else "{}",
        )
        connector = get_connector(config)
        try:
            result = await connector.connect()
            assert result.success, f"Connection failed: {result.message}"
        finally:
            await connector.close()


@requires_posthog
class TestPostHogIntegration:
    async def test_connect(self):
        project_id = os.environ.get("POSTHOG_PROJECT_ID", "")
        config = SourceConfig(
            source_id="integration-posthog",
            source_type="posthog",
            auth_env_var="POSTHOG_API_KEY",
            config_json=f'{{"project_id": "{project_id}"}}',
        )
        connector = get_connector(config)
        try:
            result = await connector.connect()
            assert result.success, f"Connection failed: {result.message}"
        finally:
            await connector.close()


@requires_rb2b
class TestRB2BIntegration:
    async def test_connect(self):
        config = SourceConfig(
            source_id="integration-rb2b",
            source_type="rb2b",
            auth_env_var="RB2B_API_KEY",
        )
        connector = get_connector(config)
        try:
            result = await connector.connect()
            assert result.success, f"Connection failed: {result.message}"
        finally:
            await connector.close()
