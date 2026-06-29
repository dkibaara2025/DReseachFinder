"""Tests for app.utils.redis_client module."""
import pytest

from app.utils.redis_client import cache_get, cache_set, rate_limit_check


class TestRedisClientFallbacks:
    """Test Redis client gracefully handles unavailable Redis."""

    @pytest.mark.asyncio
    async def test_cache_get_returns_none_without_redis(self):
        result = await cache_get("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_set_returns_false_without_redis(self):
        result = await cache_set("key", "value", ttl=60)
        assert result is False

    @pytest.mark.asyncio
    async def test_rate_limit_allows_without_redis(self):
        result = await rate_limit_check("rate_key", limit=10, window=60)
        assert result is True
