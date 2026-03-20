"""Access Control Engine activities — local computation, no I/O.

Run on ACCESS_ENGINE_QUEUE. These are activities called by
CheckAccessWorkflow and EvaluatePermissionsWorkflow for pure
permission evaluation logic. They never touch the network.

Activities:
  evaluate_access_decision     — check if principal has required permission
  compute_effective_permissions — aggregate all permissions for a principal
  hello_check_access           — backward-compat placeholder
"""

from __future__ import annotations

from typing import Any

from temporalio import activity

# ---------------------------------------------------------------------------
# Backward-compat stub — QueryWorkflow and ShareWorkflow still call this.
# Remove when DATA_MGR is wired to Access Engine workflows.
# ---------------------------------------------------------------------------


@activity.defn
async def hello_check_access(user_id: str) -> str:
    """Deprecated: kept for backward compatibility."""
    activity.logger.info(
        f"Access Engine: checking access for user '{user_id}'",
    )
    return f"Access granted: {user_id}"


# ---------------------------------------------------------------------------
# Local activities — pure computation, no I/O
# ---------------------------------------------------------------------------

# Permission hierarchy: admin > write > read
_PERMISSION_HIERARCHY = {"admin": 3, "write": 2, "read": 1}


def _permission_level(permission: str) -> int:
    """Return numeric level for a permission string."""
    return _PERMISSION_HIERARCHY.get(permission.lower(), 0)


def _permission_meets_requirement(
    granted: str,
    required: str,
) -> bool:
    """Check if granted permission meets or exceeds required level.

    admin grants everything. write grants read. read grants only read.
    """
    return _permission_level(granted) >= _permission_level(required)


@activity.defn
async def evaluate_access_decision(
    decision_input: dict[str, Any],
) -> dict[str, Any]:
    """Check if a principal has the required permission level.

    Input dict keys:
      permissions: list[dict] — ViewPermission-like dicts
      principal_id: str
      principal_type: str
      required_permission: str — read, write, or admin
      view: dict | None — view metadata (for view_id)

    Returns dict with:
      allowed: bool
      matched_permission: str — the permission that matched
      reason: str — human-readable explanation
    """
    permissions: list[dict[str, Any]] = decision_input.get(
        "permissions", [],
    )
    principal_id: str = decision_input.get("principal_id", "")
    required: str = decision_input.get("required_permission", "read")

    # Public views: allow read access without explicit permission
    view = decision_input.get("view")
    if (
        view
        and view.get("visibility") == "public"
        and required == "read"
    ):
        return {
            "allowed": True,
            "matched_permission": "read",
            "reason": "public view allows anonymous read",
        }

    if not principal_id:
        return {
            "allowed": False,
            "matched_permission": "",
            "reason": "no principal_id provided",
        }

    if not permissions:
        return {
            "allowed": False,
            "matched_permission": "",
            "reason": "no permissions defined for this view",
        }

    # Find matching permission for this principal
    for perm in permissions:
        perm_principal = perm.get("principal_id", "")
        perm_level = perm.get("permission", "")

        if perm_principal == principal_id:
            if _permission_meets_requirement(perm_level, required):
                return {
                    "allowed": True,
                    "matched_permission": perm_level,
                    "reason": (
                        f"{perm_level} meets required {required}"
                    ),
                }
            return {
                "allowed": False,
                "matched_permission": perm_level,
                "reason": (
                    f"{perm_level} does not meet required {required}"
                ),
            }

    return {
        "allowed": False,
        "matched_permission": "",
        "reason": f"no permission grant found for {principal_id}",
    }


@activity.defn
async def compute_effective_permissions(
    perms_input: dict[str, Any],
) -> dict[str, Any]:
    """Aggregate effective permissions for a principal.

    Input dict keys:
      permissions: list[dict] — ViewPermission-like dicts
      principal_id: str
      principal_type: str
      resource_type: str | None — optional filter

    Returns dict with:
      view_ids: list[str]
      permission_levels: dict[str, str] — view_id → effective level
      total_count: int
    """
    permissions: list[dict[str, Any]] = perms_input.get(
        "permissions", [],
    )
    principal_id: str = perms_input.get("principal_id", "")

    if not principal_id or not permissions:
        return {
            "view_ids": [],
            "permission_levels": {},
            "total_count": 0,
        }

    # Collect all grants for this principal, dedup by view_id
    effective: dict[str, str] = {}  # view_id → highest permission
    for perm in permissions:
        if perm.get("principal_id") != principal_id:
            continue

        view_id = perm.get("view_id", "")
        perm_level = perm.get("permission", "")

        if not view_id:
            continue

        # Take the highest permission if multiple grants exist
        existing = effective.get(view_id, "")
        if _permission_level(perm_level) > _permission_level(existing):
            effective[view_id] = perm_level

    # Apply resource_type filter if specified
    # (would filter by view metadata in a richer implementation,
    # but for now all views pass since we don't have type info)

    view_ids = sorted(effective.keys())
    return {
        "view_ids": view_ids,
        "permission_levels": effective,
        "total_count": len(view_ids),
    }
