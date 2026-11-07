"""Focused tests for cache-aside behavior."""

import json
from typing import Any

import pytest
from backend.cache import JsonCache
from backend.settings import Settings
from redis.exceptions import ConnectionError as RedisConnectionError


class MemoryRedis:
    """Minimal async Redis test double with SET NX support."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, name: str) -> str | None:
        return self.values.get(name)

    async def set(
        self,
        name: str,
        value: str,
        *,
        ex: int | None = None,
        nx: bool = False,
    ) -> bool:
        del ex
        if nx and name in self.values:
            return False
        self.values[name] = value
        return True

    async def delete(self, *names: str) -> int:
        deleted = 0
        for name in names:
            deleted += int(self.values.pop(name, None) is not None)
        return deleted

    async def eval(
        self,
        _script: str,
        _numkeys: int,
        key: str,
        token: str,
    ) -> int:
        if self.values.get(key) != token:
            return 0
        return await self.delete(key)


def settings(**overrides: Any) -> Settings:
    defaults = {
        "_env_file": None,
        "cache_ttl_jitter_ratio": 0,
        "cache_lock_wait_seconds": 0,
    }
    return Settings(**defaults, **overrides)


@pytest.mark.asyncio
async def test_cache_miss_then_hit_uses_versioned_key() -> None:
    redis = MemoryRedis()
    cache = JsonCache(redis, settings(cache_version="v7"), clock=lambda: 1000)
    calls = 0

    async def fetch() -> dict[str, int]:
        nonlocal calls
        calls += 1
        return {"value": calls}

    first = await cache.get_or_fetch("weather:psi", {"region": "all"}, fetch)
    second = await cache.get_or_fetch("weather:psi", {"region": "all"}, fetch)

    assert first.data == {"value": 1}
    assert first.meta.state == "miss"
    assert second.data == {"value": 1}
    assert second.meta.state == "hit"
    assert second.meta.key.startswith("lta:v7:weather:psi:")
    assert calls == 1


@pytest.mark.asyncio
async def test_stale_value_is_returned_when_refresh_fails() -> None:
    redis = MemoryRedis()
    cache = JsonCache(redis, settings(), clock=lambda: 1100)
    key = cache.make_key("traffic:incidents", {})
    await redis.set(
        f"{key}:stale",
        json.dumps({"data": {"old": True}, "fetched_at": 1000}),
    )

    async def fail() -> None:
        raise RuntimeError("provider failed")

    result = await cache.get_or_fetch("traffic:incidents", {}, fail)

    assert result.data == {"old": True}
    assert result.meta.state == "stale-if-error"
    assert result.meta.stale is True
    assert result.meta.age_seconds == 100


@pytest.mark.asyncio
async def test_existing_lock_serves_stale_without_duplicate_fetch() -> None:
    redis = MemoryRedis()
    cache = JsonCache(redis, settings(), clock=lambda: 1100)
    key = cache.make_key("rail:crowding", {"line": "EWL"})
    await redis.set(f"{key}:lock", "other-worker")
    await redis.set(
        f"{key}:stale",
        json.dumps({"data": {"level": "m"}, "fetched_at": 1000}),
    )
    called = False

    async def fetch() -> dict[str, str]:
        nonlocal called
        called = True
        return {"level": "h"}

    result = await cache.get_or_fetch(
        "rail:crowding",
        {"line": "EWL"},
        fetch,
    )

    assert result.meta.state == "stale-while-locked"
    assert result.data == {"level": "m"}
    assert called is False


@pytest.mark.asyncio
async def test_redis_failure_degrades_to_upstream() -> None:
    class BrokenRedis(MemoryRedis):
        async def get(self, name: str) -> str | None:
            del name
            raise RedisConnectionError("offline")

    cache = JsonCache(BrokenRedis(), settings(), clock=lambda: 1000)

    async def fetch() -> dict[str, bool]:
        return {"fresh": True}

    result = await cache.get_or_fetch("weather:uv", {}, fetch)

    assert result.data == {"fresh": True}
    assert result.meta.state == "degraded"
    assert result.meta.redis_degraded is True
