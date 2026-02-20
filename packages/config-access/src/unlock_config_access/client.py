"""Redis client adapter for Config Access activities.

Normalizes the interface between Upstash SDK (cloud) and fakeredis (local dev).
Both support get/set/zadd/sadd/hset/hdel etc., but differ on transactions:
  - Upstash: multi() → tx.execute() (returns list of results)
  - redis-py/fakeredis: pipeline(transaction=True) → pipe.execute()

The RedisAdapter wraps this difference so activities never touch raw clients.

Environment detection:
  - UPSTASH_REDIS_REST_URL set → Upstash SDK (staging/prod/PR preview)
  - Otherwise → fakeredis (local dev, no Docker, no cloud dependency)

Usage in activities:
    from unlock_config_access.client import get_client

    client = get_client()
    await client.set("cfg:schema:123", json_str)
    value = await client.get("cfg:schema:123")
"""

from __future__ import annotations

import os
from typing import Any


class RedisTransaction:
    """Wraps either an Upstash multi or a fakeredis pipeline for uniform tx API."""

    def __init__(self, raw_tx: Any, is_upstash: bool) -> None:
        self._tx = raw_tx
        self._is_upstash = is_upstash

    def set(self, key: str, value: str) -> RedisTransaction:
        self._tx.set(key, value)
        return self

    def delete(self, key: str) -> RedisTransaction:
        self._tx.delete(key)
        return self

    def zadd(self, key: str, mapping: dict[str, float]) -> RedisTransaction:
        if self._is_upstash:
            for member, score in mapping.items():
                self._tx.zadd(key, {"member": member, "score": score})
        else:
            self._tx.zadd(key, mapping)
        return self

    def sadd(self, key: str, *members: str) -> RedisTransaction:
        self._tx.sadd(key, *members)
        return self

    def srem(self, key: str, *members: str) -> RedisTransaction:
        self._tx.srem(key, *members)
        return self

    def hset(self, key: str, field: str, value: str) -> RedisTransaction:
        self._tx.hset(key, field, value)
        return self

    def hdel(self, key: str, *fields: str) -> RedisTransaction:
        self._tx.hdel(key, *fields)
        return self

    async def execute(self) -> list[Any]:
        if self._is_upstash:
            return await self._tx.exec()
        else:
            return await self._tx.execute()


class RedisAdapter:
    """Unified async Redis interface over Upstash SDK or fakeredis."""

    def __init__(self, raw_client: Any, is_upstash: bool = False) -> None:
        self._client = raw_client
        self._is_upstash = is_upstash

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(self, key: str, value: str) -> None:
        await self._client.set(key, value)

    async def delete(self, *keys: str) -> None:
        await self._client.delete(*keys)

    async def zadd(self, key: str, mapping: dict[str, float]) -> None:
        if self._is_upstash:
            for member, score in mapping.items():
                await self._client.zadd(key, {"member": member, "score": score})
        else:
            await self._client.zadd(key, mapping)

    async def zrangebyscore(
        self, key: str, min_score: float, max_score: float, start: int = 0, num: int = -1
    ) -> list[str]:
        if self._is_upstash:
            result = await self._client.zrangebyscore(
                key, min_score, max_score, offset=start, count=num
            )
        else:
            result = await self._client.zrangebyscore(
                key, min_score, max_score, start=start, num=num
            )
        return [r if isinstance(r, str) else r.decode() for r in (result or [])]

    async def zcard(self, key: str) -> int:
        return await self._client.zcard(key) or 0

    async def zrange(self, key: str, start: int, stop: int) -> list[str]:
        result = await self._client.zrange(key, start, stop)
        return [r if isinstance(r, str) else r.decode() for r in (result or [])]

    async def sadd(self, key: str, *members: str) -> None:
        await self._client.sadd(key, *members)

    async def srem(self, key: str, *members: str) -> None:
        await self._client.srem(key, *members)

    async def smembers(self, key: str) -> set[str]:
        result = await self._client.smembers(key)
        return {r if isinstance(r, str) else r.decode() for r in (result or set())}

    async def scard(self, key: str) -> int:
        return await self._client.scard(key) or 0

    async def hset(self, key: str, field: str, value: str) -> None:
        await self._client.hset(key, field, value)

    async def hget(self, key: str, field: str) -> str | None:
        return await self._client.hget(key, field)

    async def hdel(self, key: str, *fields: str) -> None:
        await self._client.hdel(key, *fields)

    async def hgetall(self, key: str) -> dict[str, str]:
        result = await self._client.hgetall(key)
        if not result:
            return {}
        if isinstance(result, dict):
            return {
                (k if isinstance(k, str) else k.decode()): (v if isinstance(v, str) else v.decode())
                for k, v in result.items()
            }
        return {}

    def multi(self) -> RedisTransaction:
        if self._is_upstash:
            return RedisTransaction(self._client.multi(), is_upstash=True)
        else:
            return RedisTransaction(
                self._client.pipeline(transaction=True), is_upstash=False
            )


# ============================================================================
# Singleton management
# ============================================================================

_client: RedisAdapter | None = None


def get_client() -> RedisAdapter:
    """Return a lazily-initialized RedisAdapter singleton.

    Environment detection:
      - UPSTASH_REDIS_REST_URL set → Upstash SDK
      - Otherwise → fakeredis (in-memory, no external dependency)
    """
    global _client
    if _client is not None:
        return _client

    if os.environ.get("UPSTASH_REDIS_REST_URL"):
        from upstash_redis.asyncio import Redis

        raw = Redis.from_env()
        _client = RedisAdapter(raw, is_upstash=True)
    else:
        from fakeredis.aioredis import FakeRedis

        raw = FakeRedis(decode_responses=True)
        _client = RedisAdapter(raw, is_upstash=False)

    return _client


def reset_client() -> None:
    """Reset the client singleton — used in tests to inject mocks."""
    global _client
    _client = None


def set_client(adapter: RedisAdapter) -> None:
    """Inject a client — used in tests."""
    global _client
    _client = adapter
