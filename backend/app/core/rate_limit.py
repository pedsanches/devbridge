"""
Rate limiting utilities.

Provides Redis-backed rate limiting with in-memory fallback.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    reset_at: int


def build_rate_limit_headers(result: RateLimitResult) -> dict[str, str]:
    """Build standard rate limit headers."""
    return {
        "X-RateLimit-Limit": str(result.limit),
        "X-RateLimit-Remaining": str(result.remaining),
        "X-RateLimit-Reset": str(result.reset_at),
    }


class RateLimiter:
    """Rate limiter with Redis backend and local fallback."""

    def __init__(self) -> None:
        self._redis_by_loop: dict[int, Redis[str]] = {}
        self._local_counters: dict[str, deque[float]] = {}
        self._local_lock = asyncio.Lock()

    async def check(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        """
        Check and increment a rate limit bucket.

        Args:
            key: Unique rate limit key.
            limit: Max requests allowed per window.
            window_seconds: Window duration in seconds.

        Returns:
            RateLimitResult with current allowance.
        """
        if limit <= 0:
            now = int(time.time())
            return RateLimitResult(allowed=True, limit=limit, remaining=0, reset_at=now)

        count, reset_in = await self._increment(key, window_seconds)
        remaining = max(limit - count, 0)
        reset_at = int(time.time()) + max(reset_in, 0)
        return RateLimitResult(
            allowed=count <= limit,
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
        )

    async def _increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        if settings.REDIS_URL:
            try:
                redis = await self._get_redis()
                return await self._increment_redis(redis, key, window_seconds)
            except RedisError as exc:
                logger.warning(
                    "Redis rate limit failed, falling back to memory",
                    error=str(exc),
                )
        return await self._increment_local(key, window_seconds)

    async def _get_redis(self) -> Redis[str]:
        loop_id = id(asyncio.get_running_loop())
        redis = self._redis_by_loop.get(loop_id)
        if redis is None:
            redis = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            self._redis_by_loop[loop_id] = redis
        return redis

    @staticmethod
    async def _increment_redis(
        redis: Redis[str],
        key: str,
        window_seconds: int,
    ) -> tuple[int, int]:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds)
        ttl = await redis.ttl(key)
        reset_in = window_seconds if ttl is None or ttl < 0 else ttl
        return int(count), int(reset_in)

    async def _increment_local(self, key: str, window_seconds: int) -> tuple[int, int]:
        now = time.monotonic()
        async with self._local_lock:
            bucket = self._local_counters.setdefault(key, deque())
            cutoff = now - window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            bucket.append(now)
            count = len(bucket)
            oldest = bucket[0] if bucket else now
            reset_in = int(max(window_seconds - (now - oldest), 0))
            return count, reset_in


rate_limiter = RateLimiter()
