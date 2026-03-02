"""Schema Evolution Engine activities — local computation, no I/O.

Run on SCHEMA_ENGINE_QUEUE. These are activities called by
GenerateMappingsWorkflow and ValidateSchemaWorkflow for pure schema
analysis logic. They never touch the network.

Activities:
  generate_field_mappings    — match source→target by name/type similarity
  validate_and_detect_drift  — check records against schema, detect drift
  hello_validate_schema      — backward-compat placeholder
"""

from __future__ import annotations

from typing import Any

from temporalio import activity

# ---------------------------------------------------------------------------
# Backward-compat stub — QueryWorkflow still dispatches to this.
# Remove when DATA_MGR is wired to Schema Engine workflows.
# ---------------------------------------------------------------------------


@activity.defn
async def hello_validate_schema(data_ref: str) -> str:
    """Deprecated: kept for QueryWorkflow backward compatibility."""
    activity.logger.info(
        f"Schema Engine: validating schema for '{data_ref}'",
    )
    return f"Schema valid: {data_ref}"


# ---------------------------------------------------------------------------
# Local activities — pure computation, no I/O
# ---------------------------------------------------------------------------

# Type compatibility matrix: source_type → set of compatible target types
_TYPE_COMPAT: dict[str, set[str]] = {
    "string": {"string"},
    "integer": {"integer", "number", "float", "string"},
    "number": {"number", "float", "integer", "string"},
    "float": {"float", "number", "string"},
    "boolean": {"boolean", "string"},
    "datetime": {"datetime", "string"},
    "date": {"date", "datetime", "string"},
    "array": {"array", "string"},
    "object": {"object", "string"},
}

# Suggested transforms based on type pairs
_TRANSFORM_SUGGESTIONS: dict[tuple[str, str], str] = {
    ("string", "string"): "trim",
    ("integer", "string"): "to_string",
    ("number", "string"): "to_string",
    ("float", "string"): "to_string",
    ("datetime", "string"): "to_string",
    ("string", "integer"): "to_int",
    ("string", "float"): "to_float",
    ("string", "datetime"): "parse_date",
}


def _normalize_name(name: str) -> str:
    """Normalize field name for matching: lowercase, strip underscores."""
    return name.lower().replace("_", "").replace("-", "")


def _name_similarity(source: str, target: str) -> float:
    """Score name similarity: 1.0 = exact, 0.8 = case-insensitive, etc."""
    if source == target:
        return 1.0
    if source.lower() == target.lower():
        return 0.9
    if _normalize_name(source) == _normalize_name(target):
        return 0.8
    # Check if one contains the other
    ns, nt = _normalize_name(source), _normalize_name(target)
    if ns in nt or nt in ns:
        return 0.5
    return 0.0


def _types_compatible(source_type: str, target_type: str) -> bool:
    """Check if source type can be mapped to target type."""
    if not source_type or not target_type:
        return True  # unknown types are compatible by default
    compat = _TYPE_COMPAT.get(source_type.lower(), {"string"})
    return target_type.lower() in compat


@activity.defn
async def generate_field_mappings(
    mapping_input: dict[str, Any],
) -> dict[str, Any]:
    """Match source fields to target fields by name/type similarity.

    Input dict keys:
      source_fields: dict[str, str] — {field_name: inferred_type}
      target_fields: dict[str, str] — {field_name: expected_type}

    Returns dict with:
      mappings: list[dict] — FieldMapping-compatible dicts
      unmapped_source: list[str]
      unmapped_target: list[str]
    """
    source_fields: dict[str, str] = mapping_input.get(
        "source_fields", {},
    )
    target_fields: dict[str, str] = mapping_input.get(
        "target_fields", {},
    )

    # If no target fields, create identity mappings from source
    if not target_fields:
        mappings = [
            {
                "source_field": name,
                "target_field": name,
                "transform": None,
            }
            for name in source_fields
        ]
        return {
            "mappings": mappings,
            "unmapped_source": [],
            "unmapped_target": [],
        }

    mappings: list[dict[str, Any]] = []
    matched_sources: set[str] = set()
    matched_targets: set[str] = set()

    # Score all source→target pairs and pick best matches
    candidates: list[tuple[float, str, str]] = []
    for src_name, src_type in source_fields.items():
        for tgt_name, tgt_type in target_fields.items():
            score = _name_similarity(src_name, tgt_name)
            if score > 0 and _types_compatible(src_type, tgt_type):
                candidates.append((score, src_name, tgt_name))

    # Sort by score descending, pick best non-conflicting matches
    candidates.sort(key=lambda x: x[0], reverse=True)
    for _score, src_name, tgt_name in candidates:
        if src_name in matched_sources or tgt_name in matched_targets:
            continue
        matched_sources.add(src_name)
        matched_targets.add(tgt_name)

        src_type = source_fields.get(src_name, "")
        tgt_type = target_fields.get(tgt_name, "")
        transform = _TRANSFORM_SUGGESTIONS.get(
            (src_type.lower(), tgt_type.lower()),
        )

        mappings.append({
            "source_field": src_name,
            "target_field": tgt_name,
            "transform": transform,
        })

    unmapped_source = [
        n for n in source_fields if n not in matched_sources
    ]
    unmapped_target = [
        n for n in target_fields if n not in matched_targets
    ]

    return {
        "mappings": mappings,
        "unmapped_source": unmapped_source,
        "unmapped_target": unmapped_target,
    }


@activity.defn
async def validate_and_detect_drift(
    validate_input: dict[str, Any],
) -> dict[str, Any]:
    """Validate records against schema definition and detect drift.

    Input dict keys:
      schema_def: dict — SchemaDefinition-like dict with 'fields' list
      records: list[dict] — records to validate

    Returns dict with:
      valid_count: int
      invalid_count: int
      drift: dict — DriftReport-like dict
    """
    schema_def: dict[str, Any] = validate_input.get("schema_def", {})
    records: list[dict[str, Any]] = validate_input.get("records", [])

    # Extract expected fields from schema definition
    expected_fields: dict[str, str] = {}
    for field in schema_def.get("fields", []):
        name = field.get("target_field") or field.get("source_field", "")
        if name:
            expected_fields[name] = field.get("transform", "string")

    if not records:
        return {
            "valid_count": 0,
            "invalid_count": 0,
            "drift": {
                "has_drift": False,
                "new_fields": [],
                "missing_fields": [],
                "type_changes": [],
                "sample_size": 0,
            },
        }

    # Validate each record and collect all observed fields
    valid_count = 0
    invalid_count = 0
    all_observed_fields: set[str] = set()

    for record in records:
        record_fields = set(record.keys())
        all_observed_fields.update(record_fields)

        # A record is valid if all expected fields are present
        missing = set(expected_fields.keys()) - record_fields
        if not missing:
            valid_count += 1
        else:
            invalid_count += 1

    # Detect drift
    expected_set = set(expected_fields.keys())
    new_fields = sorted(all_observed_fields - expected_set)
    missing_fields = sorted(expected_set - all_observed_fields)

    has_drift = bool(new_fields or missing_fields)

    return {
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "drift": {
            "has_drift": has_drift,
            "new_fields": new_fields,
            "missing_fields": missing_fields,
            "type_changes": [],
            "sample_size": len(records),
        },
    }
