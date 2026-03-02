"""Transformation Engine activities — local computation, no I/O.

Run on TRANSFORM_ENGINE_QUEUE. These are local activities called by
TransformWorkflow for pure data transformation logic. They never touch
the network — all I/O goes through RA activities on their respective queues.

Activities:
  apply_transform_rules — apply ordered pipeline rules to records
  validate_pipeline     — dry-run validation of transform rule configuration
  hello_transform       — backward-compat placeholder (IngestWorkflow still calls it)
"""

from __future__ import annotations

import contextlib
from typing import Any

from temporalio import activity

# ---------------------------------------------------------------------------
# Backward-compat stub — IngestWorkflow still dispatches to this.
# Remove when DATA_MGR is wired to TransformWorkflow.
# ---------------------------------------------------------------------------


@activity.defn
async def hello_transform(raw_data: str) -> str:
    """Deprecated: kept for IngestWorkflow backward compatibility."""
    activity.logger.info(f"Transform Engine: transforming '{raw_data[:50]}'")
    return f"Transformed: {raw_data}"


# ---------------------------------------------------------------------------
# Local activities — pure computation, no I/O
# ---------------------------------------------------------------------------

# Valid rule types and their required config keys
_RULE_TYPES = {
    "map": set(),  # uses field_mappings from pipeline_def
    "filter": {"expression"},
    "aggregate": {"group_by", "operation"},
    "enrich": {"field", "expression"},
    "deduplicate": {"key_fields"},
}

_VALID_OPERATIONS = {"sum", "count", "avg", "min", "max"}
_VALID_TRANSFORMS = {
    "lowercase", "uppercase", "trim", "parse_date",
    "to_string", "to_int", "to_float",
}


def _apply_map_rule(
    records: list[dict[str, Any]],
    rule_config: dict[str, Any],
    field_mappings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Rename/convert fields per FieldMappings."""
    if not field_mappings:
        return records

    result = []
    for record in records:
        new_record = dict(record)
        for mapping in field_mappings:
            src = mapping.get("source_field", "")
            tgt = mapping.get("target_field", "")
            transform = mapping.get("transform")
            default = mapping.get("default_value")

            if not src or not tgt:
                continue

            value = record.get(src, default)

            if value is not None and transform:
                value = _apply_field_transform(value, transform)

            if value is not None:
                new_record[tgt] = value
                if src != tgt and src in new_record:
                    del new_record[src]

        result.append(new_record)
    return result


def _apply_field_transform(value: Any, transform: str) -> Any:
    """Apply a single field-level transform."""
    if transform == "lowercase" and isinstance(value, str):
        return value.lower()
    if transform == "uppercase" and isinstance(value, str):
        return value.upper()
    if transform == "trim" and isinstance(value, str):
        return value.strip()
    if transform == "to_string":
        return str(value)
    if transform == "to_int":
        try:
            return int(value)
        except (ValueError, TypeError):
            return value
    if transform == "to_float":
        try:
            return float(value)
        except (ValueError, TypeError):
            return value
    return value


def _try_numeric_compare(
    record: dict[str, Any],
    record_value: Any,
    operator: str,
    value: str,
    result: list[dict[str, Any]],
) -> None:
    """Attempt numeric comparison; silently skip on type errors."""
    try:
        rv = float(record_value) if record_value is not None else None
        cv = float(value)
        if rv is not None and _numeric_op(rv, operator, cv):
            result.append(record)
    except (ValueError, TypeError):
        pass


def _numeric_op(rv: float, operator: str, cv: float) -> bool:
    if operator == ">":
        return rv > cv
    if operator == "<":
        return rv < cv
    if operator == ">=":
        return rv >= cv
    return rv <= cv  # operator == "<="


def _matches_filter(
    record_value: Any,
    operator: str,
    value: str,
) -> bool | None:
    """Check if a record value matches a filter operator.

    Returns True/False for definitive matches, None for numeric operators
    that need special handling (try/except for type conversion).
    """
    if operator == "exists":
        return record_value is not None
    if operator == "not_exists":
        return record_value is None
    if operator == "==":
        return str(record_value) == value
    if operator == "!=":
        return str(record_value) != value
    if operator == "contains":
        return isinstance(record_value, str) and value in record_value
    if operator == "not_contains":
        return isinstance(record_value, str) and value not in record_value
    return None  # numeric operators handled separately


def _apply_filter_rule(
    records: list[dict[str, Any]],
    rule_config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Keep records matching a filter expression.

    Expression format: "field_name operator value"
    Operators: ==, !=, >, <, >=, <=, contains, not_contains,
               exists, not_exists
    """
    expr = rule_config.get("expression", "")
    if not expr:
        return records

    parts = expr.split(None, 2)
    if len(parts) < 2:
        return records

    field_name = parts[0]
    operator = parts[1]
    value = parts[2] if len(parts) > 2 else ""

    result: list[dict[str, Any]] = []
    for record in records:
        record_value = record.get(field_name)
        match = _matches_filter(record_value, operator, value)

        if match is True:
            result.append(record)
        elif match is None and operator in (">", "<", ">=", "<="):
            _try_numeric_compare(
                record, record_value, operator, value, result,
            )

    return result


def _apply_aggregate_rule(
    records: list[dict[str, Any]],
    rule_config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Group by key fields, compute aggregate operation."""
    group_by_str = rule_config.get("group_by", "")
    operation = rule_config.get("operation", "count")
    value_field = rule_config.get("value_field", "")

    if not group_by_str:
        return records

    group_fields = [f.strip() for f in group_by_str.split(",")]
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}

    for record in records:
        key = tuple(record.get(f) for f in group_fields)
        groups.setdefault(key, []).append(record)

    result = []
    for key, group_records in groups.items():
        agg_record: dict[str, Any] = {}
        for i, f in enumerate(group_fields):
            agg_record[f] = key[i]

        if operation == "count":
            agg_record["count"] = len(group_records)
        elif operation in ("sum", "avg", "min", "max") and value_field:
            values = []
            for r in group_records:
                v = r.get(value_field)
                if v is not None:
                    with contextlib.suppress(ValueError, TypeError):
                        values.append(float(v))
            if values:
                if operation == "sum":
                    agg_record[f"{operation}_{value_field}"] = sum(values)
                elif operation == "avg":
                    agg_record[f"{operation}_{value_field}"] = sum(values) / len(values)
                elif operation == "min":
                    agg_record[f"{operation}_{value_field}"] = min(values)
                elif operation == "max":
                    agg_record[f"{operation}_{value_field}"] = max(values)
            else:
                agg_record[f"{operation}_{value_field}"] = 0

        result.append(agg_record)

    return result


def _apply_enrich_rule(
    records: list[dict[str, Any]],
    rule_config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Add computed/derived fields from existing fields.

    Expression format: "source_field_1 + source_field_2" (concatenation for strings)
    or "source_field_1" (copy)
    """
    field_name = rule_config.get("field", "")
    expression = rule_config.get("expression", "")
    if not field_name or not expression:
        return records

    result = []
    for record in records:
        new_record = dict(record)
        if " + " in expression:
            parts = [p.strip() for p in expression.split(" + ")]
            values = [str(record.get(p, "")) for p in parts]
            new_record[field_name] = " ".join(v for v in values if v)
        else:
            new_record[field_name] = record.get(expression)
        result.append(new_record)

    return result


def _apply_deduplicate_rule(
    records: list[dict[str, Any]],
    rule_config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Remove duplicates by key fields."""
    key_fields_str = rule_config.get("key_fields", "")
    if not key_fields_str:
        return records

    key_fields = [f.strip() for f in key_fields_str.split(",")]
    seen: set[tuple[Any, ...]] = set()
    result = []

    for record in records:
        key = tuple(record.get(f) for f in key_fields)
        if key not in seen:
            seen.add(key)
            result.append(record)

    return result


@activity.defn
async def apply_transform_rules(transform_input: dict[str, Any]) -> dict[str, Any]:
    """Apply ordered pipeline rules to records. Pure computation — no I/O.

    Input dict keys:
      records: list[dict] — the records to transform
      pipeline_def: dict — pipeline definition with transform_rules and fields

    Returns dict with:
      success: bool
      records: list[dict] — transformed records
      rules_applied: int
      message: str
    """
    records: list[dict[str, Any]] = transform_input.get("records", [])
    pipeline_def: dict[str, Any] = transform_input.get("pipeline_def", {})

    transform_rules = pipeline_def.get("transform_rules", [])
    field_mappings = pipeline_def.get("fields", [])

    if not records:
        return {
            "success": True,
            "records": [],
            "rules_applied": 0,
            "message": "No records to transform",
        }

    # Sort rules by order
    sorted_rules = sorted(transform_rules, key=lambda r: r.get("order", 0))

    current_records = list(records)
    rules_applied = 0

    for rule in sorted_rules:
        rule_type = rule.get("rule_type", "")
        config = rule.get("config", {})

        if rule_type == "map":
            current_records = _apply_map_rule(current_records, config, field_mappings)
        elif rule_type == "filter":
            current_records = _apply_filter_rule(current_records, config)
        elif rule_type == "aggregate":
            current_records = _apply_aggregate_rule(current_records, config)
        elif rule_type == "enrich":
            current_records = _apply_enrich_rule(current_records, config)
        elif rule_type == "deduplicate":
            current_records = _apply_deduplicate_rule(current_records, config)
        else:
            activity.logger.warning(f"Unknown rule type: {rule_type}")
            continue

        rules_applied += 1

    return {
        "success": True,
        "records": current_records,
        "rules_applied": rules_applied,
        "message": (
            f"Applied {rules_applied} rules to {len(records)} "
            f"records → {len(current_records)}"
        ),
    }


@activity.defn
async def validate_pipeline(validate_input: dict[str, Any]) -> dict[str, Any]:
    """Dry-run validation of transform rule configuration. No I/O.

    Input dict keys:
      transform_rules: list[dict] — rules to validate
      field_mappings: list[dict] — optional field mappings
      sample_record: dict | None — optional sample for dry-run

    Returns dict with:
      success: bool
      is_valid: bool
      errors: list[str]
      warnings: list[str]
    """
    transform_rules = validate_input.get("transform_rules", [])
    field_mappings = validate_input.get("field_mappings", [])
    sample_record = validate_input.get("sample_record")

    errors: list[str] = []
    warnings: list[str] = []

    if not transform_rules:
        errors.append("No transform rules provided")
        return {
            "success": True,
            "is_valid": False,
            "errors": errors,
            "warnings": warnings,
        }

    for i, rule in enumerate(transform_rules):
        rule_type = rule.get("rule_type", "")
        config = rule.get("config", {})

        if rule_type not in _RULE_TYPES:
            errors.append(f"Rule {i}: unknown rule_type '{rule_type}'")
            continue

        required_keys = _RULE_TYPES[rule_type]
        for key in required_keys:
            if key not in config:
                errors.append(f"Rule {i} ({rule_type}): missing required config key '{key}'")

        if rule_type == "aggregate":
            op = config.get("operation", "")
            if op and op not in _VALID_OPERATIONS:
                errors.append(f"Rule {i} (aggregate): unknown operation '{op}'")

        if rule_type == "map" and not field_mappings:
            warnings.append(f"Rule {i} (map): no field_mappings provided, rule will be a no-op")

    # Validate field mappings
    for i, mapping in enumerate(field_mappings):
        if not mapping.get("source_field"):
            errors.append(f"FieldMapping {i}: missing source_field")
        if not mapping.get("target_field"):
            errors.append(f"FieldMapping {i}: missing target_field")
        transform = mapping.get("transform")
        if transform and transform not in _VALID_TRANSFORMS:
            warnings.append(f"FieldMapping {i}: unknown transform '{transform}'")

    is_valid = len(errors) == 0

    # Optional dry-run on sample record
    if is_valid and sample_record is not None:
        try:
            test_pipeline = {"transform_rules": transform_rules, "fields": field_mappings}
            result = await apply_transform_rules(
                {"records": [sample_record], "pipeline_def": test_pipeline}
            )
            if not result["success"]:
                errors.append(f"Dry-run failed: {result.get('message', '')}")
                is_valid = False
        except Exception as e:
            errors.append(f"Dry-run exception: {e}")
            is_valid = False

    return {
        "success": True,
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
    }
