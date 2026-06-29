import logging

import redis.asyncio as redis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis | None:
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.redis_url, decode_responses=True
            )
            await _redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            _redis_client = None
    return _redis_client


async def cache_get(key: str) -> str | None:
    r = await get_redis()
    if r:
        try:
            return await r.get(key)
        except Exception:
            return None
    return None


async def cache_set(key: str, value: str, ttl: int = 3600) -> bool:
    r = await get_redis()
    if r:
        try:
            await r.set(key, value, ex=ttl)
            return True
        except Exception:
            return False
    return False


async def rate_limit_check(key: str, limit: int = 60, window: int = 60) -> bool:
    """Simple rate limiter. Returns True if request is allowed."""
    r = await get_redis()
    if not r:
        return True  # Allow if Redis unavailable
    try:
        current = await r.incr(key)
        if current == 1:
            await r.expire(key, window)
        return current <= limit
    except Exception:
        return True
