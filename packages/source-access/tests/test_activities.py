"""Tests for Source Access Temporal activity functions.

These test the activity layer — the bridge between Temporal workflows and
connectors. Connectors are mocked to isolate the activity logic:
  - Argument deserialization from Temporal
  - Connector lifecycle (create, delegate, close)
  - Error propagation
"""

from unittest.mock import AsyncMock, patch

import pytest
from unlock_shared.source_models import (
    ConnectionResult,
    FetchRequest,
    FetchResult,
    SourceConfig,
    SourceSchema,
)
from unlock_source_access.activities import (
    connect_source,
    fetch_source_data,
    get_source_schema,
)

# Aliased to avoid pytest collecting it as a test function (name starts with "test_")
from unlock_source_access.activities import test_connection as activity_test_connection


@pytest.fixture
def mock_connector():
    """Create a mock connector with async methods."""
    connector = AsyncMock()
    connector.connect = AsyncMock(
        return_value=ConnectionResult(
            success=True,
            message="Mock connected",
            source_id="test",
            source_type="unipile",
        )
    )
    connector.test_connection = AsyncMock(
        return_value=ConnectionResult(
            success=True,
            message="Mock test OK",
            source_id="test",
            source_type="unipile",
        )
    )
    connector.fetch_data = AsyncMock(
        return_value=FetchResult(
            success=True,
            message="Fetched 5 records",
            source_id="test",
            records=[{"id": str(i)} for i in range(5)],
            record_count=5,
        )
    )
    connector.get_schema = AsyncMock(
        return_value=SourceSchema(
            success=True,
            message="Found 3 fields",
            source_id="test",
            fields={"id": "str", "name": "str", "count": "int"},
        )
    )
    connector.close = AsyncMock()
    return connector


@pytest.fixture
def source_config():
    return SourceConfig(
        source_id="test",
        source_type="unipile",
        auth_env_var="UNIPILE_API_KEY",
    )


@pytest.fixture
def fetch_request():
    return FetchRequest(
        source_id="test",
        source_type="unipile",
        resource_type="posts",
        auth_env_var="UNIPILE_API_KEY",
    )


class TestConnectSourceActivity:
    @patch("unlock_source_access.activities.get_connector")
    async def test_connect_success(self, mock_factory, mock_connector, source_config):
        mock_factory.return_value = mock_connector

        result = await connect_source(source_config)
        assert result.success
        assert result.message == "Mock connected"
        mock_connector.close.assert_called_once()

    @patch("unlock_source_access.activities.get_connector")
    async def test_connect_always_closes(self, mock_factory, source_config):
        """Connector is closed even if connect() raises."""
        connector = AsyncMock()
        connector.connect = AsyncMock(side_effect=RuntimeError("boom"))
        connector.close = AsyncMock()
        mock_factory.return_value = connector

        with pytest.raises(RuntimeError, match="boom"):
            await connect_source(source_config)
        connector.close.assert_called_once()


class TestFetchSourceDataActivity:
    @patch("unlock_source_access.activities.get_connector")
    async def test_fetch_success(self, mock_factory, mock_connector, fetch_request):
        mock_factory.return_value = mock_connector

        result = await fetch_source_data(fetch_request)
        assert result.success
        assert result.record_count == 5
        mock_connector.close.assert_called_once()

    @patch("unlock_source_access.activities.get_connector")
    async def test_fetch_builds_config_from_request(self, mock_factory, mock_connector):
        """The activity builds a SourceConfig from FetchRequest fields."""
        mock_factory.return_value = mock_connector

        request = FetchRequest(
            source_id="custom",
            source_type="x",
            resource_type="tweets",
            auth_env_var="X_BEARER_TOKEN",
            base_url="https://custom.api/v2/",
            config_json='{"user_id": "123"}',
            rate_limit_per_second=2.0,
        )
        await fetch_source_data(request)

        # Verify the factory received a SourceConfig with the right fields
        call_args = mock_factory.call_args[0][0]
        assert call_args.source_id == "custom"
        assert call_args.source_type == "x"
        assert call_args.base_url == "https://custom.api/v2/"
        assert call_args.rate_limit_per_second == 2.0


class TestTestConnectionActivity:
    @patch("unlock_source_access.activities.get_connector")
    async def test_test_connection_success(self, mock_factory, mock_connector, source_config):
        mock_factory.return_value = mock_connector

        result = await activity_test_connection(source_config)
        assert result.success
        mock_connector.close.assert_called_once()


class TestGetSourceSchemaActivity:
    @patch("unlock_source_access.activities.get_connector")
    async def test_schema_discovery(self, mock_factory, mock_connector, fetch_request):
        mock_factory.return_value = mock_connector

        result = await get_source_schema(fetch_request)
        assert result.success
        assert len(result.fields) == 3
        mock_connector.close.assert_called_once()


class TestActivityErrorHandling:
    @patch("unlock_source_access.activities.get_connector")
    async def test_unknown_source_type(self, mock_factory):
        """Factory raises ValueError for unknown source type — activity propagates."""
        mock_factory.side_effect = ValueError("Unknown source_type 'bogus'")

        config = SourceConfig(source_id="bad", source_type="bogus")
        with pytest.raises(ValueError, match="Unknown source_type"):
            await connect_source(config)
