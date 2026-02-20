"""Test fixtures for Config Access activities.

Provides a MockRedis adapter that mirrors the RedisAdapter interface, recording
all operations and returning canned results. Activities call get_client() —
we patch it to return our mock.

Fixtures provide realistic civic engagement configuration objects: schemas for
community engagement analysis, pipelines for social media ingestion, views for
dashboard visualizations.
"""

from __future__ import annotations

from typing import Any

import pytest

# ============================================================================
# MockRedis — mirrors RedisAdapter interface
# ============================================================================


class MockRedisTransaction:
    """Records transaction operations for assertion."""

    def __init__(self) -> None:
        self.ops: list[tuple[str, tuple]] = []

    def set(self, key: str, value: str) -> MockRedisTransaction:
        self.ops.append(("set", (key, value)))
        return self

    def delete(self, key: str) -> MockRedisTransaction:
        self.ops.append(("delete", (key,)))
        return self

    def zadd(self, key: str, mapping: dict[str, float]) -> MockRedisTransaction:
        self.ops.append(("zadd", (key, mapping)))
        return self

    def sadd(self, key: str, *members: str) -> MockRedisTransaction:
        self.ops.append(("sadd", (key, *members)))
        return self

    def srem(self, key: str, *members: str) -> MockRedisTransaction:
        self.ops.append(("srem", (key, *members)))
        return self

    def hset(self, key: str, field: str, value: str) -> MockRedisTransaction:
        self.ops.append(("hset", (key, field, value)))
        return self

    def hdel(self, key: str, *fields: str) -> MockRedisTransaction:
        self.ops.append(("hdel", (key, *fields)))
        return self

    async def execute(self) -> list[Any]:
        return [None] * len(self.ops)


class MockRedis:
    """In-memory Redis mock that mirrors RedisAdapter's async interface.

    Stores data in plain dicts so tests can assert on stored values.
    """

    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.sorted_sets: dict[str, dict[str, float]] = {}
        self.sets: dict[str, set[str]] = {}
        self.hashes: dict[str, dict[str, str]] = {}
        self.calls: list[tuple[str, tuple]] = []

    async def get(self, key: str) -> str | None:
        self.calls.append(("get", (key,)))
        return self.store.get(key)

    async def set(self, key: str, value: str) -> None:
        self.calls.append(("set", (key, value)))
        self.store[key] = value

    async def delete(self, *keys: str) -> None:
        self.calls.append(("delete", keys))
        for key in keys:
            self.store.pop(key, None)
            self.sorted_sets.pop(key, None)
            self.sets.pop(key, None)
            self.hashes.pop(key, None)

    async def zadd(self, key: str, mapping: dict[str, float]) -> None:
        self.calls.append(("zadd", (key, mapping)))
        if key not in self.sorted_sets:
            self.sorted_sets[key] = {}
        self.sorted_sets[key].update(mapping)

    async def zrangebyscore(
        self, key: str, min_score: float, max_score: float, start: int = 0, num: int = -1
    ) -> list[str]:
        self.calls.append(("zrangebyscore", (key, min_score, max_score)))
        zset = self.sorted_sets.get(key, {})
        items = sorted(
            ((m, s) for m, s in zset.items() if min_score <= s <= max_score),
            key=lambda x: x[1],
        )
        members = [m for m, _ in items]
        if num > 0:
            return members[start:start + num]
        return members[start:]

    async def zcard(self, key: str) -> int:
        return len(self.sorted_sets.get(key, {}))

    async def zrange(self, key: str, start: int, stop: int) -> list[str]:
        self.calls.append(("zrange", (key, start, stop)))
        zset = self.sorted_sets.get(key, {})
        items = sorted(zset.items(), key=lambda x: x[1])
        members = [m for m, _ in items]
        # Redis semantics: -1 means last element (inclusive)
        if stop < 0:
            stop = len(members) + stop
        return members[start:stop + 1]

    async def sadd(self, key: str, *members: str) -> None:
        self.calls.append(("sadd", (key, *members)))
        if key not in self.sets:
            self.sets[key] = set()
        self.sets[key].update(members)

    async def srem(self, key: str, *members: str) -> None:
        self.calls.append(("srem", (key, *members)))
        if key in self.sets:
            self.sets[key] -= set(members)

    async def smembers(self, key: str) -> set[str]:
        self.calls.append(("smembers", (key,)))
        return self.sets.get(key, set()).copy()

    async def scard(self, key: str) -> int:
        return len(self.sets.get(key, set()))

    async def hset(self, key: str, field: str, value: str) -> None:
        self.calls.append(("hset", (key, field, value)))
        if key not in self.hashes:
            self.hashes[key] = {}
        self.hashes[key][field] = value

    async def hget(self, key: str, field: str) -> str | None:
        self.calls.append(("hget", (key, field)))
        return self.hashes.get(key, {}).get(field)

    async def hdel(self, key: str, *fields: str) -> None:
        self.calls.append(("hdel", (key, *fields)))
        if key in self.hashes:
            for f in fields:
                self.hashes[key].pop(f, None)

    async def hgetall(self, key: str) -> dict[str, str]:
        self.calls.append(("hgetall", (key,)))
        return dict(self.hashes.get(key, {}))

    def multi(self) -> MockRedisTransaction:
        self.calls.append(("multi", ()))
        return MockRedisTransaction()


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_redis() -> MockRedis:
    """Provide a fresh MockRedis for each test."""
    return MockRedis()


@pytest.fixture
def community_engagement_schema() -> dict[str, str | int | list | None]:
    """A realistic schema for analyzing community engagement across channels."""
    return {
        "name": "Community Engagement Analysis",
        "description": "Tracks civic engagement across LinkedIn, X, and email channels",
        "schema_type": "analysis",
        "fields": [
            {"source_field": "platform_user_id", "target_field": "contact_id", "transform": None},
            {"source_field": "post_text", "target_field": "content_body", "transform": "lowercase"},
            {
                "source_field": "reaction_count",
                "target_field": "engagement_score",
                "transform": None,
            },
        ],
        "funnel_stages": [
            {"name": "Awareness", "description": "First contact with content", "order": 0},
            {"name": "Interaction", "description": "Liked, commented, or shared", "order": 1},
            {"name": "Participation", "description": "Attended event or workshop", "order": 2},
            {"name": "Advocacy", "description": "Created content or recruited others", "order": 3},
        ],
    }


@pytest.fixture
def linkedin_pipeline() -> dict[str, str | int | list | None]:
    """A realistic pipeline for ingesting LinkedIn posts via Unipile."""
    return {
        "name": "LinkedIn Post Ingestion",
        "description": "Transforms raw Unipile LinkedIn posts into engagement graph records",
        "source_type": "unipile",
        "transform_rules": [
            {"rule_type": "map", "config": {"source": "text", "target": "body"}, "order": 0},
            {"rule_type": "filter", "config": {"min_reactions": 1}, "order": 1},
            {"rule_type": "enrich", "config": {"llm_classify": True}, "order": 2},
        ],
        "schedule_cron": "0 */6 * * *",
    }


@pytest.fixture
def dashboard_view() -> dict[str, str | dict | None]:
    """A realistic view for an engagement dashboard."""
    return {
        "name": "Alabama Civic Engagement Dashboard",
        "description": "Overview of civic engagement across all channels in Alabama",
        "schema_id": "placeholder",  # replaced in tests with actual schema ID
        "filters": {"state": "AL", "status": "active"},
        "layout_config": {"chart_type": "bar", "group_by": "channel", "time_range": "30d"},
    }
