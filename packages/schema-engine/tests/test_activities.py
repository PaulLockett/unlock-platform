"""Tests for Schema Engine local activities — pure computation, no mocks needed.

Tests generate_field_mappings and validate_and_detect_drift directly.
No Temporal, no Redis, no SQL — just input → output.
"""

import pytest
from unlock_schema_engine.activities import (
    generate_field_mappings,
    hello_validate_schema,
    validate_and_detect_drift,
)

# ---------------------------------------------------------------------------
# hello_validate_schema backward compat
# ---------------------------------------------------------------------------


class TestHelloValidateSchema:
    @pytest.mark.asyncio
    async def test_returns_valid_string(self):
        result = await hello_validate_schema("test-ref")
        assert result == "Schema valid: test-ref"


# ---------------------------------------------------------------------------
# generate_field_mappings
# ---------------------------------------------------------------------------


class TestGenerateFieldMappings:
    @pytest.mark.asyncio
    async def test_identity_mappings_when_no_target(self):
        """No target fields → identity mappings from source."""
        result = await generate_field_mappings({
            "source_fields": {"name": "string", "age": "integer"},
            "target_fields": {},
        })
        assert len(result["mappings"]) == 2
        assert result["unmapped_source"] == []
        assert result["unmapped_target"] == []

    @pytest.mark.asyncio
    async def test_exact_name_match(self):
        result = await generate_field_mappings({
            "source_fields": {"email": "string", "name": "string"},
            "target_fields": {"email": "string", "name": "string"},
        })
        assert len(result["mappings"]) == 2
        names = {m["source_field"] for m in result["mappings"]}
        assert names == {"email", "name"}

    @pytest.mark.asyncio
    async def test_case_insensitive_match(self):
        result = await generate_field_mappings({
            "source_fields": {"Email": "string"},
            "target_fields": {"email": "string"},
        })
        assert len(result["mappings"]) == 1
        assert result["mappings"][0]["source_field"] == "Email"
        assert result["mappings"][0]["target_field"] == "email"

    @pytest.mark.asyncio
    async def test_snake_camel_match(self):
        """first_name matches firstname (normalized)."""
        result = await generate_field_mappings({
            "source_fields": {"first_name": "string"},
            "target_fields": {"firstname": "string"},
        })
        assert len(result["mappings"]) == 1

    @pytest.mark.asyncio
    async def test_unmapped_fields(self):
        result = await generate_field_mappings({
            "source_fields": {
                "email": "string",
                "extra_source": "string",
            },
            "target_fields": {
                "email": "string",
                "extra_target": "string",
            },
        })
        assert len(result["mappings"]) == 1
        assert "extra_source" in result["unmapped_source"]
        assert "extra_target" in result["unmapped_target"]

    @pytest.mark.asyncio
    async def test_type_compatibility_integer_to_number(self):
        result = await generate_field_mappings({
            "source_fields": {"count": "integer"},
            "target_fields": {"count": "number"},
        })
        assert len(result["mappings"]) == 1

    @pytest.mark.asyncio
    async def test_empty_source_fields(self):
        result = await generate_field_mappings({
            "source_fields": {},
            "target_fields": {"name": "string"},
        })
        assert len(result["mappings"]) == 0
        assert result["unmapped_target"] == ["name"]

    @pytest.mark.asyncio
    async def test_transform_suggestion(self):
        """Integer→string mapping should suggest to_string transform."""
        result = await generate_field_mappings({
            "source_fields": {"age": "integer"},
            "target_fields": {"age": "string"},
        })
        assert len(result["mappings"]) == 1
        assert result["mappings"][0]["transform"] == "to_string"


# ---------------------------------------------------------------------------
# validate_and_detect_drift
# ---------------------------------------------------------------------------


class TestValidateAndDetectDrift:
    @pytest.mark.asyncio
    async def test_all_records_valid(self):
        result = await validate_and_detect_drift({
            "schema_def": {
                "fields": [
                    {"target_field": "name"},
                    {"target_field": "email"},
                ],
            },
            "records": [
                {"name": "Alice", "email": "a@x.com"},
                {"name": "Bob", "email": "b@x.com"},
            ],
        })
        assert result["valid_count"] == 2
        assert result["invalid_count"] == 0
        assert result["drift"]["has_drift"] is False

    @pytest.mark.asyncio
    async def test_some_records_invalid(self):
        result = await validate_and_detect_drift({
            "schema_def": {
                "fields": [
                    {"target_field": "name"},
                    {"target_field": "email"},
                ],
            },
            "records": [
                {"name": "Alice", "email": "a@x.com"},
                {"name": "Bob"},  # missing email
            ],
        })
        assert result["valid_count"] == 1
        assert result["invalid_count"] == 1

    @pytest.mark.asyncio
    async def test_drift_new_fields(self):
        result = await validate_and_detect_drift({
            "schema_def": {
                "fields": [{"target_field": "name"}],
            },
            "records": [
                {"name": "Alice", "phone": "555-1234"},
            ],
        })
        assert result["drift"]["has_drift"] is True
        assert "phone" in result["drift"]["new_fields"]

    @pytest.mark.asyncio
    async def test_drift_missing_fields(self):
        """Fields in schema but never in any record."""
        result = await validate_and_detect_drift({
            "schema_def": {
                "fields": [
                    {"target_field": "name"},
                    {"target_field": "obsolete_field"},
                ],
            },
            "records": [{"name": "Alice"}],
        })
        assert result["drift"]["has_drift"] is True
        assert "obsolete_field" in result["drift"]["missing_fields"]

    @pytest.mark.asyncio
    async def test_empty_records(self):
        result = await validate_and_detect_drift({
            "schema_def": {
                "fields": [{"target_field": "name"}],
            },
            "records": [],
        })
        assert result["valid_count"] == 0
        assert result["invalid_count"] == 0
        assert result["drift"]["has_drift"] is False

    @pytest.mark.asyncio
    async def test_no_drift(self):
        """Records exactly match schema — no new or missing fields."""
        result = await validate_and_detect_drift({
            "schema_def": {
                "fields": [
                    {"target_field": "a"},
                    {"target_field": "b"},
                ],
            },
            "records": [
                {"a": 1, "b": 2},
                {"a": 3, "b": 4},
            ],
        })
        assert result["drift"]["has_drift"] is False
        assert result["drift"]["new_fields"] == []
        assert result["drift"]["missing_fields"] == []
