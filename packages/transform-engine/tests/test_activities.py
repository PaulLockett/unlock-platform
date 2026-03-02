"""Tests for Transform Engine local activities — pure computation, no mocks needed.

Tests apply_transform_rules and validate_pipeline directly as functions.
No Temporal, no Redis, no SQL — just input → output.
"""

import pytest
from unlock_transform_engine.activities import (
    apply_transform_rules,
    hello_transform,
    validate_pipeline,
)

# ---------------------------------------------------------------------------
# hello_transform backward compat
# ---------------------------------------------------------------------------


class TestHelloTransform:
    @pytest.mark.asyncio
    async def test_returns_transformed_string(self):
        result = await hello_transform("some raw data")
        assert result == "Transformed: some raw data"

    @pytest.mark.asyncio
    async def test_handles_empty_string(self):
        result = await hello_transform("")
        assert result == "Transformed: "


# ---------------------------------------------------------------------------
# apply_transform_rules
# ---------------------------------------------------------------------------


class TestApplyTransformRules:
    @pytest.mark.asyncio
    async def test_empty_records(self):
        result = await apply_transform_rules({"records": [], "pipeline_def": {}})
        assert result["success"] is True
        assert result["records"] == []
        assert result["rules_applied"] == 0

    @pytest.mark.asyncio
    async def test_no_rules(self):
        records = [{"name": "Alice", "age": 30}]
        result = await apply_transform_rules({
            "records": records,
            "pipeline_def": {"transform_rules": []},
        })
        assert result["success"] is True
        assert result["records"] == records
        assert result["rules_applied"] == 0

    @pytest.mark.asyncio
    async def test_map_rule_renames_field(self):
        records = [{"text": "hello", "count": 5}]
        pipeline = {
            "transform_rules": [{"rule_type": "map", "config": {}, "order": 0}],
            "fields": [
                {"source_field": "text", "target_field": "body", "transform": None},
            ],
        }
        result = await apply_transform_rules({"records": records, "pipeline_def": pipeline})
        assert result["success"] is True
        assert result["rules_applied"] == 1
        assert result["records"][0]["body"] == "hello"
        assert "text" not in result["records"][0]

    @pytest.mark.asyncio
    async def test_map_rule_with_lowercase_transform(self):
        records = [{"Name": "ALICE"}]
        pipeline = {
            "transform_rules": [{"rule_type": "map", "config": {}, "order": 0}],
            "fields": [
                {"source_field": "Name", "target_field": "name", "transform": "lowercase"},
            ],
        }
        result = await apply_transform_rules({"records": records, "pipeline_def": pipeline})
        assert result["records"][0]["name"] == "alice"

    @pytest.mark.asyncio
    async def test_map_rule_with_trim_transform(self):
        records = [{"raw": "  spaced  "}]
        pipeline = {
            "transform_rules": [{"rule_type": "map", "config": {}, "order": 0}],
            "fields": [
                {"source_field": "raw", "target_field": "clean", "transform": "trim"},
            ],
        }
        result = await apply_transform_rules({"records": records, "pipeline_def": pipeline})
        assert result["records"][0]["clean"] == "spaced"

    @pytest.mark.asyncio
    async def test_filter_rule_equality(self):
        records = [
            {"status": "active", "name": "a"},
            {"status": "inactive", "name": "b"},
            {"status": "active", "name": "c"},
        ]
        pipeline = {
            "transform_rules": [
                {"rule_type": "filter", "config": {"expression": "status == active"}, "order": 0},
            ],
        }
        result = await apply_transform_rules({"records": records, "pipeline_def": pipeline})
        assert len(result["records"]) == 2
        assert all(r["status"] == "active" for r in result["records"])

    @pytest.mark.asyncio
    async def test_filter_rule_exists(self):
        records = [
            {"name": "a", "email": "a@x.com"},
            {"name": "b"},
        ]
        pipeline = {
            "transform_rules": [
                {"rule_type": "filter", "config": {"expression": "email exists"}, "order": 0},
            ],
        }
        result = await apply_transform_rules({"records": records, "pipeline_def": pipeline})
        assert len(result["records"]) == 1
        assert result["records"][0]["name"] == "a"

    @pytest.mark.asyncio
    async def test_filter_rule_numeric_comparison(self):
        records = [
            {"name": "a", "score": 80},
            {"name": "b", "score": 30},
            {"name": "c", "score": 90},
        ]
        pipeline = {
            "transform_rules": [
                {"rule_type": "filter", "config": {"expression": "score >= 50"}, "order": 0},
            ],
        }
        result = await apply_transform_rules({"records": records, "pipeline_def": pipeline})
        assert len(result["records"]) == 2

    @pytest.mark.asyncio
    async def test_aggregate_rule_count(self):
        records = [
            {"city": "Birmingham", "type": "event"},
            {"city": "Birmingham", "type": "meeting"},
            {"city": "Huntsville", "type": "event"},
        ]
        pipeline = {
            "transform_rules": [
                {
                    "rule_type": "aggregate",
                    "config": {"group_by": "city", "operation": "count"},
                    "order": 0,
                },
            ],
        }
        result = await apply_transform_rules({"records": records, "pipeline_def": pipeline})
        assert len(result["records"]) == 2
        by_city = {r["city"]: r["count"] for r in result["records"]}
        assert by_city["Birmingham"] == 2
        assert by_city["Huntsville"] == 1

    @pytest.mark.asyncio
    async def test_aggregate_rule_sum(self):
        records = [
            {"city": "A", "amount": 10},
            {"city": "A", "amount": 20},
            {"city": "B", "amount": 5},
        ]
        pipeline = {
            "transform_rules": [
                {
                    "rule_type": "aggregate",
                    "config": {
                        "group_by": "city",
                        "operation": "sum",
                        "value_field": "amount",
                    },
                    "order": 0,
                },
            ],
        }
        result = await apply_transform_rules({"records": records, "pipeline_def": pipeline})
        by_city = {r["city"]: r for r in result["records"]}
        assert by_city["A"]["sum_amount"] == 30
        assert by_city["B"]["sum_amount"] == 5

    @pytest.mark.asyncio
    async def test_enrich_rule_copy_field(self):
        records = [{"first": "Alice", "last": "Smith"}]
        pipeline = {
            "transform_rules": [
                {
                    "rule_type": "enrich",
                    "config": {"field": "full_name", "expression": "first + last"},
                    "order": 0,
                },
            ],
        }
        result = await apply_transform_rules({"records": records, "pipeline_def": pipeline})
        assert result["records"][0]["full_name"] == "Alice Smith"

    @pytest.mark.asyncio
    async def test_deduplicate_rule(self):
        records = [
            {"email": "a@x.com", "name": "Alice"},
            {"email": "b@x.com", "name": "Bob"},
            {"email": "a@x.com", "name": "Alice Again"},
        ]
        pipeline = {
            "transform_rules": [
                {
                    "rule_type": "deduplicate",
                    "config": {"key_fields": "email"},
                    "order": 0,
                },
            ],
        }
        result = await apply_transform_rules({"records": records, "pipeline_def": pipeline})
        assert len(result["records"]) == 2
        assert result["records"][0]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_chained_rules_in_order(self):
        """Filter then map — order matters."""
        records = [
            {"status": "active", "Name": "ALICE"},
            {"status": "inactive", "Name": "BOB"},
        ]
        pipeline = {
            "transform_rules": [
                {"rule_type": "filter", "config": {"expression": "status == active"}, "order": 1},
                {"rule_type": "map", "config": {}, "order": 2},
            ],
            "fields": [
                {"source_field": "Name", "target_field": "name", "transform": "lowercase"},
            ],
        }
        result = await apply_transform_rules({"records": records, "pipeline_def": pipeline})
        assert len(result["records"]) == 1
        assert result["records"][0]["name"] == "alice"
        assert result["rules_applied"] == 2

    @pytest.mark.asyncio
    async def test_unknown_rule_type_skipped(self):
        records = [{"x": 1}]
        pipeline = {
            "transform_rules": [{"rule_type": "unknown_type", "config": {}, "order": 0}],
        }
        result = await apply_transform_rules({"records": records, "pipeline_def": pipeline})
        assert result["success"] is True
        assert result["rules_applied"] == 0
        assert result["records"] == records


# ---------------------------------------------------------------------------
# validate_pipeline
# ---------------------------------------------------------------------------


class TestValidatePipeline:
    @pytest.mark.asyncio
    async def test_empty_rules_invalid(self):
        result = await validate_pipeline({"transform_rules": []})
        assert result["is_valid"] is False
        assert any("No transform rules" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_valid_filter_rule(self):
        result = await validate_pipeline({
            "transform_rules": [
                {"rule_type": "filter", "config": {"expression": "status == active"}},
            ],
        })
        assert result["is_valid"] is True
        assert result["errors"] == []

    @pytest.mark.asyncio
    async def test_unknown_rule_type(self):
        result = await validate_pipeline({
            "transform_rules": [{"rule_type": "bogus", "config": {}}],
        })
        assert result["is_valid"] is False
        assert any("unknown rule_type" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_missing_required_config_key(self):
        result = await validate_pipeline({
            "transform_rules": [{"rule_type": "filter", "config": {}}],
        })
        assert result["is_valid"] is False
        assert any("expression" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_aggregate_unknown_operation(self):
        result = await validate_pipeline({
            "transform_rules": [
                {
                    "rule_type": "aggregate",
                    "config": {"group_by": "city", "operation": "median"},
                },
            ],
        })
        assert result["is_valid"] is False
        assert any("unknown operation" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_map_without_mappings_warns(self):
        result = await validate_pipeline({
            "transform_rules": [{"rule_type": "map", "config": {}}],
            "field_mappings": [],
        })
        assert result["is_valid"] is True
        assert any("no-op" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_field_mapping_missing_source(self):
        result = await validate_pipeline({
            "transform_rules": [{"rule_type": "map", "config": {}}],
            "field_mappings": [{"source_field": "", "target_field": "body"}],
        })
        assert result["is_valid"] is False
        assert any("source_field" in e for e in result["errors"])

    @pytest.mark.asyncio
    async def test_dry_run_with_sample_record(self):
        result = await validate_pipeline({
            "transform_rules": [
                {"rule_type": "filter", "config": {"expression": "status == active"}},
            ],
            "sample_record": {"status": "active", "name": "test"},
        })
        assert result["is_valid"] is True
