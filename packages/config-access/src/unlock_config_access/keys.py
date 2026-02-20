"""Redis key patterns for Config Access.

All keys use the `cfg:` prefix. JSON strings for objects, sorted sets + sets
for indexes. Key functions are pure — they compute key names, never touch Redis.

Righting Software test: if we switched to PostgreSQL, these would become table/column
names. The naming reflects domain concepts (schema, pipeline, view, perm), not
Redis-specific concepts (hash, zset).
"""


# ============================================================================
# Schema keys
# ============================================================================


def schema_key(schema_id: str) -> str:
    """Current version of a schema definition."""
    return f"cfg:schema:{schema_id}"


def schema_version_key(schema_id: str, version: int) -> str:
    """Immutable version snapshot of a schema."""
    return f"cfg:schema:{schema_id}:v{version}"


def schema_idx_all() -> str:
    """Sorted set of all schema IDs (score = timestamp)."""
    return "cfg:schema:idx:all"


def schema_idx_status(status: str) -> str:
    """Set of schema IDs with a given status."""
    return f"cfg:schema:idx:status:{status}"


def schema_idx_name(name: str) -> str:
    """String lookup: schema name → schema ID."""
    return f"cfg:schema:idx:name:{name}"


# ============================================================================
# Pipeline keys
# ============================================================================


def pipeline_key(pipeline_id: str) -> str:
    """Current version of a pipeline definition."""
    return f"cfg:pipeline:{pipeline_id}"


def pipeline_version_key(pipeline_id: str, version: int) -> str:
    """Immutable version snapshot of a pipeline."""
    return f"cfg:pipeline:{pipeline_id}:v{version}"


def pipeline_idx_all() -> str:
    """Sorted set of all pipeline IDs (score = timestamp)."""
    return "cfg:pipeline:idx:all"


def pipeline_idx_source(source_type: str) -> str:
    """String lookup: source type → active pipeline ID."""
    return f"cfg:pipeline:idx:source:{source_type}"


def pipeline_idx_status(status: str) -> str:
    """Set of pipeline IDs with a given status."""
    return f"cfg:pipeline:idx:status:{status}"


# ============================================================================
# View keys
# ============================================================================


def view_key(view_id: str) -> str:
    """View definition."""
    return f"cfg:view:{view_id}"


def view_idx_all() -> str:
    """Sorted set of all view IDs (score = timestamp)."""
    return "cfg:view:idx:all"


def view_idx_token(token: str) -> str:
    """String lookup: share token → view ID."""
    return f"cfg:view:idx:token:{token}"


def view_idx_schema(schema_id: str) -> str:
    """Set of view IDs using a given schema."""
    return f"cfg:view:idx:schema:{schema_id}"


def view_idx_status(status: str) -> str:
    """Set of view IDs with a given status."""
    return f"cfg:view:idx:status:{status}"


def view_idx_clones(source_view_id: str) -> str:
    """Set of view IDs cloned from a given source view."""
    return f"cfg:view:idx:clones:{source_view_id}"


# ============================================================================
# Permission keys
# ============================================================================


def perm_key(view_id: str) -> str:
    """Hash: principal_id → JSON permission for a view."""
    return f"cfg:perm:{view_id}"


def perm_idx_principal(principal_id: str) -> str:
    """Set of view IDs a principal has access to."""
    return f"cfg:perm:idx:principal:{principal_id}"
