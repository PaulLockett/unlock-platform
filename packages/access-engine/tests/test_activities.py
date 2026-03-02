"""Tests for Access Engine activities — pure computation, no I/O.

evaluate_access_decision and compute_effective_permissions are local
activities that implement permission logic. No mocking needed — just
input dict → output dict.
"""

from __future__ import annotations

import pytest
from unlock_access_engine.activities import (
    compute_effective_permissions,
    evaluate_access_decision,
    hello_check_access,
)

# ============================================================================
# hello_check_access (backward compat)
# ============================================================================


class TestHelloCheckAccess:
    """Deprecated shim kept for backward compatibility."""

    @pytest.mark.asyncio
    async def test_returns_granted(self):
        result = await hello_check_access("user-123")
        assert result == "Access granted: user-123"

    @pytest.mark.asyncio
    async def test_empty_user(self):
        result = await hello_check_access("")
        assert "Access granted" in result


# ============================================================================
# evaluate_access_decision
# ============================================================================


class TestEvaluateAccessDecision:
    """Binary access check: does principal have required permission?"""

    @pytest.mark.asyncio
    async def test_allowed_exact_match(self):
        """read permission meets read requirement."""
        result = await evaluate_access_decision({
            "permissions": [
                {"principal_id": "user-1", "permission": "read"},
            ],
            "principal_id": "user-1",
            "required_permission": "read",
        })
        assert result["allowed"] is True
        assert result["matched_permission"] == "read"

    @pytest.mark.asyncio
    async def test_allowed_admin_grants_read(self):
        """admin permission exceeds read requirement."""
        result = await evaluate_access_decision({
            "permissions": [
                {"principal_id": "user-1", "permission": "admin"},
            ],
            "principal_id": "user-1",
            "required_permission": "read",
        })
        assert result["allowed"] is True
        assert result["matched_permission"] == "admin"

    @pytest.mark.asyncio
    async def test_allowed_admin_grants_write(self):
        """admin permission exceeds write requirement."""
        result = await evaluate_access_decision({
            "permissions": [
                {"principal_id": "user-1", "permission": "admin"},
            ],
            "principal_id": "user-1",
            "required_permission": "write",
        })
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_allowed_write_grants_read(self):
        """write permission exceeds read requirement."""
        result = await evaluate_access_decision({
            "permissions": [
                {"principal_id": "user-1", "permission": "write"},
            ],
            "principal_id": "user-1",
            "required_permission": "read",
        })
        assert result["allowed"] is True
        assert result["matched_permission"] == "write"

    @pytest.mark.asyncio
    async def test_denied_insufficient_level(self):
        """read permission does not meet write requirement."""
        result = await evaluate_access_decision({
            "permissions": [
                {"principal_id": "user-1", "permission": "read"},
            ],
            "principal_id": "user-1",
            "required_permission": "write",
        })
        assert result["allowed"] is False
        assert result["matched_permission"] == "read"
        assert "does not meet" in result["reason"]

    @pytest.mark.asyncio
    async def test_denied_no_matching_principal(self):
        """No permission grant for this principal."""
        result = await evaluate_access_decision({
            "permissions": [
                {"principal_id": "user-other", "permission": "admin"},
            ],
            "principal_id": "user-1",
            "required_permission": "read",
        })
        assert result["allowed"] is False
        assert result["matched_permission"] == ""
        assert "no permission grant" in result["reason"]

    @pytest.mark.asyncio
    async def test_denied_no_permissions(self):
        """Empty permissions list."""
        result = await evaluate_access_decision({
            "permissions": [],
            "principal_id": "user-1",
            "required_permission": "read",
        })
        assert result["allowed"] is False
        assert "no permissions defined" in result["reason"]

    @pytest.mark.asyncio
    async def test_denied_no_principal_id(self):
        """Missing principal_id."""
        result = await evaluate_access_decision({
            "permissions": [
                {"principal_id": "user-1", "permission": "admin"},
            ],
            "principal_id": "",
            "required_permission": "read",
        })
        assert result["allowed"] is False
        assert "no principal_id" in result["reason"]

    @pytest.mark.asyncio
    async def test_defaults_to_read(self):
        """When required_permission is omitted, defaults to read."""
        result = await evaluate_access_decision({
            "permissions": [
                {"principal_id": "user-1", "permission": "read"},
            ],
            "principal_id": "user-1",
        })
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_case_insensitive_permission(self):
        """Permission levels are case-insensitive."""
        result = await evaluate_access_decision({
            "permissions": [
                {"principal_id": "user-1", "permission": "Admin"},
            ],
            "principal_id": "user-1",
            "required_permission": "READ",
        })
        assert result["allowed"] is True


# ============================================================================
# compute_effective_permissions
# ============================================================================


class TestComputeEffectivePermissions:
    """Aggregate effective permissions for a principal."""

    @pytest.mark.asyncio
    async def test_single_grant(self):
        result = await compute_effective_permissions({
            "permissions": [
                {
                    "principal_id": "user-1",
                    "permission": "read",
                    "view_id": "view-a",
                },
            ],
            "principal_id": "user-1",
        })
        assert result["view_ids"] == ["view-a"]
        assert result["permission_levels"] == {"view-a": "read"}
        assert result["total_count"] == 1

    @pytest.mark.asyncio
    async def test_multiple_views(self):
        result = await compute_effective_permissions({
            "permissions": [
                {
                    "principal_id": "user-1",
                    "permission": "read",
                    "view_id": "view-a",
                },
                {
                    "principal_id": "user-1",
                    "permission": "write",
                    "view_id": "view-b",
                },
                {
                    "principal_id": "user-1",
                    "permission": "admin",
                    "view_id": "view-c",
                },
            ],
            "principal_id": "user-1",
        })
        assert sorted(result["view_ids"]) == [
            "view-a", "view-b", "view-c",
        ]
        assert result["total_count"] == 3

    @pytest.mark.asyncio
    async def test_dedup_takes_highest(self):
        """Multiple grants for same view — highest wins."""
        result = await compute_effective_permissions({
            "permissions": [
                {
                    "principal_id": "user-1",
                    "permission": "read",
                    "view_id": "view-a",
                },
                {
                    "principal_id": "user-1",
                    "permission": "write",
                    "view_id": "view-a",
                },
            ],
            "principal_id": "user-1",
        })
        assert result["view_ids"] == ["view-a"]
        assert result["permission_levels"]["view-a"] == "write"
        assert result["total_count"] == 1

    @pytest.mark.asyncio
    async def test_filters_by_principal(self):
        """Only returns grants for the specified principal."""
        result = await compute_effective_permissions({
            "permissions": [
                {
                    "principal_id": "user-1",
                    "permission": "admin",
                    "view_id": "view-a",
                },
                {
                    "principal_id": "user-2",
                    "permission": "admin",
                    "view_id": "view-b",
                },
            ],
            "principal_id": "user-1",
        })
        assert result["view_ids"] == ["view-a"]
        assert result["total_count"] == 1

    @pytest.mark.asyncio
    async def test_empty_permissions(self):
        result = await compute_effective_permissions({
            "permissions": [],
            "principal_id": "user-1",
        })
        assert result["view_ids"] == []
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_no_principal_id(self):
        result = await compute_effective_permissions({
            "permissions": [
                {
                    "principal_id": "user-1",
                    "permission": "read",
                    "view_id": "view-a",
                },
            ],
            "principal_id": "",
        })
        assert result["view_ids"] == []
        assert result["total_count"] == 0

    @pytest.mark.asyncio
    async def test_skips_entries_without_view_id(self):
        """Permissions without view_id are ignored."""
        result = await compute_effective_permissions({
            "permissions": [
                {
                    "principal_id": "user-1",
                    "permission": "read",
                    "view_id": "",
                },
                {
                    "principal_id": "user-1",
                    "permission": "write",
                    "view_id": "view-a",
                },
            ],
            "principal_id": "user-1",
        })
        assert result["view_ids"] == ["view-a"]
        assert result["total_count"] == 1
