"""Redis-backed asynchronous JSON cache-aside implementation."""

import asyncio
import hashlib
import json
import random
import secrets
import time
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime
from typing import Any, Protocol

from redis.exceptions import RedisError

from backend.models import ApiResponse, CacheMetadata, CacheState
from backend.settings import Settings


class AsyncRedis(Protocol):
    """Subset of the redis.asyncio API used by the cache."""

    async def get(self, name: str) -> bytes | str | None:
        """Get one value."""

    async def set(
        self,
        name: str,
        value: str,
        *,
        ex: int | None = None,
        nx: bool = False,
    ) -> Any:
        """Set one value."""

    async def delete(self, *names: str) -> int:
        """Delete values."""

    async def eval(
        self,
        script: str,
        numkeys: int,
        *keys_and_args: str,
    ) -> Any:
        """Evaluate a Lua script."""


class JsonCache:
    """Cache JSON values with stampede protection and stale fallback."""

    _UNLOCK_SCRIPT = (
        "if redis.call('get', KEYS[1]) == ARGV[1] then "
        "return redis.call('del', KEYS[1]) else return 0 end"
    )

    def __init__(
        self,
        redis_client: AsyncRedis | None,
        settings: Settings,
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.redis = redis_client
        self.settings = settings
        self.clock = clock
        self.degraded = False

    def make_key(
        self,
        namespace: str,
        parameters: Mapping[str, Any] | None = None,
    ) -> str:
        """Build a deterministic, versioned key without leaking query values."""
        canonical = json.dumps(
            parameters or {},
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20]
        safe_namespace = namespace.strip(":").replace(" ", "-")
        return f"lta:{self.settings.cache_version}:{safe_namespace}:{digest}"

    async def get_or_fetch(
        self,
        namespace: str,
        parameters: Mapping[str, Any] | None,
        fetcher: Callable[[], Awaitable[Any]],
        *,
        ttl_seconds: int | None = None,
        stale_seconds: int | None = None,
    ) -> ApiResponse:
        """Return a cached value or fetch, cache, and describe a new value."""
        key = self.make_key(namespace, parameters)
        ttl = ttl_seconds or self.settings.cache_ttl_seconds
        stale_ttl = stale_seconds or self.settings.cache_stale_seconds

        if self.redis is None:
            data = await fetcher()
            return self._response(data, key, self.clock(), "bypass")

        fresh = await self._read(key)
        if fresh is not None:
            return self._from_record(fresh, key, "hit")

        stale_key = f"{key}:stale"
        stale = await self._read(stale_key)
        if self.degraded:
            data = await fetcher()
            return self._response(
                data,
                key,
                self.clock(),
                "degraded",
                redis_degraded=True,
            )

        lock_key = f"{key}:lock"
        token = secrets.token_urlsafe(18)
        lock_state = await self._acquire_lock(lock_key, token)
        if lock_state is None:
            data = await fetcher()
            return self._response(
                data,
                key,
                self.clock(),
                "degraded",
                redis_degraded=True,
            )

        if lock_state:
            try:
                try:
                    data = await fetcher()
                except Exception:
                    if stale is not None:
                        return self._from_record(
                            stale,
                            key,
                            "stale-if-error",
                            stale=True,
                        )
                    raise

                fetched_at = self.clock()
                record = {"data": data, "fetched_at": fetched_at}
                await self._write(key, record, self._jittered_ttl(ttl))
                await self._write(stale_key, record, ttl + stale_ttl)
                return self._response(data, key, fetched_at, "miss")
            finally:
                await self._release_lock(lock_key, token)

        waited = await self._wait_for_value(key)
        if waited is not None:
            return self._from_record(waited, key, "hit")
        if stale is not None:
            return self._from_record(
                stale,
                key,
                "stale-while-locked",
                stale=True,
            )

        data = await fetcher()
        return self._response(data, key, self.clock(), "bypass")

    def _jittered_ttl(self, ttl: int) -> int:
        ratio = self.settings.cache_ttl_jitter_ratio
        multiplier = random.uniform(1 - ratio, 1 + ratio)
        return max(1, round(ttl * multiplier))

    async def _read(self, key: str) -> dict[str, Any] | None:
        if self.redis is None:
            return None
        try:
            raw = await self.redis.get(key)
            if raw is None:
                return None
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            value = json.loads(raw)
            if not isinstance(value, dict) or "fetched_at" not in value:
                await self.redis.delete(key)
                return None
            return value
        except (RedisError, OSError, ValueError, TypeError):
            self.degraded = True
            return None

    async def _write(
        self,
        key: str,
        record: dict[str, Any],
        ttl: int,
    ) -> None:
        if self.redis is None or self.degraded:
            return
        try:
            await self.redis.set(
                key,
                json.dumps(record, separators=(",", ":"), default=str),
                ex=ttl,
            )
        except (RedisError, OSError, TypeError):
            self.degraded = True

    async def _acquire_lock(self, key: str, token: str) -> bool | None:
        if self.redis is None:
            return None
        try:
            result = await self.redis.set(
                key,
                token,
                ex=self.settings.cache_lock_seconds,
                nx=True,
            )
            return bool(result)
        except (RedisError, OSError):
            self.degraded = True
            return None

    async def _release_lock(self, key: str, token: str) -> None:
        if self.redis is None or self.degraded:
            return
        try:
            await self.redis.eval(self._UNLOCK_SCRIPT, 1, key, token)
        except (RedisError, OSError, NotImplementedError):
            try:
                current = await self.redis.get(key)
                if current in (token, token.encode("utf-8")):
                    await self.redis.delete(key)
            except (RedisError, OSError):
                self.degraded = True

    async def _wait_for_value(self, key: str) -> dict[str, Any] | None:
        deadline = time.monotonic() + self.settings.cache_lock_wait_seconds
        while time.monotonic() < deadline:
            await asyncio.sleep(0.05)
            record = await self._read(key)
            if record is not None:
                return record
            if self.degraded:
                return None
        return None

    def _from_record(
        self,
        record: dict[str, Any],
        key: str,
        state: CacheState,
        *,
        stale: bool = False,
    ) -> ApiResponse:
        return self._response(
            record.get("data"),
            key,
            float(record["fetched_at"]),
            state,
            stale=stale,
        )

    def _response(
        self,
        data: Any,
        key: str,
        fetched_at: float,
        state: CacheState,
        *,
        stale: bool = False,
        redis_degraded: bool = False,
    ) -> ApiResponse:
        age = max(0.0, self.clock() - fetched_at)
        metadata = CacheMetadata(
            state=state,
            key=key,
            fetched_at=datetime.fromtimestamp(fetched_at, tz=UTC),
            age_seconds=round(age, 3),
            stale=stale,
            redis_degraded=redis_degraded,
        )
        return ApiResponse(data=data, meta=metadata)
