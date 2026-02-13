"""Shared test fixtures for Source Access tests.

Provides:
  - JSON fixture loading helpers
  - Mock HTTP transport for httpx (intercepts all requests)
  - Pre-built SourceConfig instances for each connector type
  - Environment variable setup for credential resolution
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from unlock_shared.source_models import FetchRequest, SourceConfig

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, Any]:
    """Load a JSON fixture file by name."""
    return json.loads((FIXTURES_DIR / name).read_text())


def load_fixture_raw(name: str) -> str:
    """Load a fixture file as raw text."""
    return (FIXTURES_DIR / name).read_text()


class MockTransport(httpx.AsyncBaseTransport):
    """Mock HTTP transport that returns preconfigured responses.

    Usage:
        transport = MockTransport(responses=[
            httpx.Response(200, json={"items": [...]}),
        ])
        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.get("https://example.com/api")

    Each call to handle_async_request pops the next response from the list.
    If the list is exhausted, returns a 500 error.
    """

    def __init__(self, responses: list[httpx.Response] | None = None) -> None:
        self.responses = list(responses or [])
        self.requests: list[httpx.Request] = []

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.responses:
            response = self.responses.pop(0)
            response.stream = httpx.ByteStream(response.content)
            return response
        return httpx.Response(500, json={"error": "No more mock responses"})


@pytest.fixture
def mock_env():
    """Set fake API credentials in environment variables."""
    env = {
        "UNIPILE_API_KEY": "test-unipile-key",
        "X_BEARER_TOKEN": "test-x-bearer-token",
        "POSTHOG_API_KEY": "phx_test-posthog-key",
        "RB2B_API_KEY": "test-rb2b-key",
    }
    with patch.dict("os.environ", env):
        yield env


@pytest.fixture
def unipile_config() -> SourceConfig:
    return SourceConfig(
        source_id="test-unipile",
        source_type="unipile",
        auth_env_var="UNIPILE_API_KEY",
        config_json='{"account_id": "acc-123"}',
    )


@pytest.fixture
def x_config() -> SourceConfig:
    return SourceConfig(
        source_id="test-x",
        source_type="x",
        auth_env_var="X_BEARER_TOKEN",
        config_json='{"user_id": "9876543210", "username": "unlockalabama"}',
    )


@pytest.fixture
def posthog_config() -> SourceConfig:
    return SourceConfig(
        source_id="test-posthog",
        source_type="posthog",
        auth_env_var="POSTHOG_API_KEY",
        config_json='{"project_id": "12345"}',
    )


@pytest.fixture
def rb2b_config() -> SourceConfig:
    return SourceConfig(
        source_id="test-rb2b",
        source_type="rb2b",
        auth_env_var="RB2B_API_KEY",
    )


@pytest.fixture
def unipile_fetch_request() -> FetchRequest:
    return FetchRequest(
        source_id="test-unipile",
        source_type="unipile",
        resource_type="posts",
        auth_env_var="UNIPILE_API_KEY",
        config_json='{"account_id": "acc-123"}',
        max_pages=2,
    )


@pytest.fixture
def x_fetch_request() -> FetchRequest:
    return FetchRequest(
        source_id="test-x",
        source_type="x",
        resource_type="tweets",
        auth_env_var="X_BEARER_TOKEN",
        config_json='{"user_id": "9876543210", "username": "unlockalabama"}',
        max_pages=2,
    )


@pytest.fixture
def posthog_fetch_request() -> FetchRequest:
    return FetchRequest(
        source_id="test-posthog",
        source_type="posthog",
        resource_type="events",
        auth_env_var="POSTHOG_API_KEY",
        config_json='{"project_id": "12345"}',
        max_pages=2,
    )


@pytest.fixture
def rb2b_fetch_request() -> FetchRequest:
    return FetchRequest(
        source_id="test-rb2b",
        source_type="rb2b",
        resource_type="ip_to_hem",
        auth_env_var="RB2B_API_KEY",
        config_json='{"ip_address": "203.0.113.42"}',
        max_pages=2,
    )
