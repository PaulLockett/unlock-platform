"""Tests for source registry activities — identify_source and register_source.

These test the activity logic with mocked Supabase client. The Supabase
interactions are the volatility being encapsulated, so we mock at that boundary.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from unlock_shared.source_models import (
    IdentifySourceRequest,
    IdentifySourceResult,
    RegisterSourceRequest,
    RegisterSourceResult,
    SourceRecord,
)


# ============================================================================
# Model tests
# ============================================================================


class TestSourceRecordModel:
    def test_defaults(self):
        r = SourceRecord()
        assert r.status == "active"
        assert r.resource_type == "posts"
        assert r.config == {}

    def test_from_dict(self):
        r = SourceRecord(
            id="src-1",
            name="Meta Ads",
            protocol="file_upload",
            status="active",
        )
        assert r.name == "Meta Ads"
        assert r.protocol == "file_upload"


class TestIdentifySourceModels:
    def test_request_defaults(self):
        req = IdentifySourceRequest()
        assert req.name is None
        assert req.source_type is None

    def test_result_defaults(self):
        r = IdentifySourceResult(success=True, message="ok")
        assert r.exact_match is None
        assert r.possible_matches == []
        assert r.all_sources is None


class TestRegisterSourceModels:
    def test_request_required_fields(self):
        req = RegisterSourceRequest(name="test", protocol="rest_api")
        assert req.name == "test"
        assert req.resource_type == "posts"

    def test_result_defaults(self):
        r = RegisterSourceResult(success=True, message="ok")
        assert r.source == {}


# ============================================================================
# Activity tests (mocked Supabase)
# ============================================================================


def _mock_supabase_table(data=None, error=None):
    """Build a mock Supabase client with a chainable table interface."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table

    # Build chainable response
    mock_response = MagicMock()
    mock_response.data = data or []

    # Chain methods return themselves for fluent interface
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.ilike.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.upsert.return_value = mock_table
    mock_table.single.return_value = mock_table
    mock_table.execute.return_value = mock_response

    return mock_client


class TestIdentifySource:
    @pytest.mark.asyncio
    async def test_list_all_sources(self):
        sources = [
            {"id": "1", "name": "Meta Ads", "protocol": "file_upload"},
            {"id": "2", "name": "Unipile", "protocol": "rest_api"},
        ]
        mock_client = _mock_supabase_table(data=sources)

        with patch(
            "unlock_source_access.activities._get_supabase_client",
            return_value=mock_client,
        ):
            from unlock_source_access.activities import identify_source

            result = await identify_source(IdentifySourceRequest())

        assert result.success is True
        assert result.all_sources is not None
        assert len(result.all_sources) == 2

    @pytest.mark.asyncio
    async def test_exact_match_by_name(self):
        source = {"id": "1", "name": "Meta Ads", "protocol": "file_upload"}
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table

        # First call: exact match
        exact_response = MagicMock()
        exact_response.data = [source]
        # Second call: partial matches
        partial_response = MagicMock()
        partial_response.data = [source]  # same source, should be filtered

        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.ilike.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.side_effect = [exact_response, partial_response]

        with patch(
            "unlock_source_access.activities._get_supabase_client",
            return_value=mock_client,
        ):
            from unlock_source_access.activities import identify_source

            result = await identify_source(
                IdentifySourceRequest(name="Meta Ads")
            )

        assert result.success is True
        assert result.exact_match is not None
        assert result.exact_match["name"] == "Meta Ads"

    @pytest.mark.asyncio
    async def test_no_match_returns_empty(self):
        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table

        empty_response = MagicMock()
        empty_response.data = []

        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.ilike.return_value = mock_table
        mock_table.execute.return_value = empty_response

        with patch(
            "unlock_source_access.activities._get_supabase_client",
            return_value=mock_client,
        ):
            from unlock_source_access.activities import identify_source

            result = await identify_source(
                IdentifySourceRequest(name="Nonexistent")
            )

        assert result.success is True
        assert result.exact_match is None
        assert len(result.possible_matches) == 0

    @pytest.mark.asyncio
    async def test_supabase_error_returns_failure(self):
        with patch(
            "unlock_source_access.activities._get_supabase_client",
            side_effect=Exception("Connection refused"),
        ):
            from unlock_source_access.activities import identify_source

            result = await identify_source(IdentifySourceRequest())

        assert result.success is False
        assert "Connection refused" in result.message


class TestRegisterSource:
    @pytest.mark.asyncio
    async def test_register_new_source(self):
        created = {
            "id": "new-1",
            "name": "Meta Ads",
            "protocol": "file_upload",
            "status": "active",
        }
        mock_client = _mock_supabase_table(data=[created])

        with patch(
            "unlock_source_access.activities._get_supabase_client",
            return_value=mock_client,
        ):
            from unlock_source_access.activities import register_source

            result = await register_source(
                RegisterSourceRequest(name="Meta Ads", protocol="file_upload")
            )

        assert result.success is True
        assert result.source["name"] == "Meta Ads"
        assert result.source["status"] == "active"

    @pytest.mark.asyncio
    async def test_upsert_existing_source(self):
        updated = {
            "id": "existing-1",
            "name": "Meta Ads",
            "protocol": "rest_api",
            "status": "active",
        }
        mock_client = _mock_supabase_table(data=[updated])

        with patch(
            "unlock_source_access.activities._get_supabase_client",
            return_value=mock_client,
        ):
            from unlock_source_access.activities import register_source

            result = await register_source(
                RegisterSourceRequest(name="Meta Ads", protocol="rest_api")
            )

        assert result.success is True
        assert result.source["protocol"] == "rest_api"

    @pytest.mark.asyncio
    async def test_register_failure(self):
        with patch(
            "unlock_source_access.activities._get_supabase_client",
            side_effect=Exception("Permission denied"),
        ):
            from unlock_source_access.activities import register_source

            result = await register_source(
                RegisterSourceRequest(name="test", protocol="rest_api")
            )

        assert result.success is False
        assert "Permission denied" in result.message
