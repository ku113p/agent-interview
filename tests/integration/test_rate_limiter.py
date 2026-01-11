import time

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis

from src.main import create_app
from src.settings import settings


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.mark.asyncio
async def test_rate_limiter_blocks_requests(redis_client: Redis, app: FastAPI) -> None:
    """
    Test that the rate limiter blocks requests after the limit is reached.
    """
    # Use a custom client IP to avoid conflict with other tests
    # ASGITransport usually sets client to ("127.0.0.1", port)
    client_ip = "127.0.0.1"

    # Let's clear any existing rate limit for this IP
    current_window = int(time.time() // 60)
    key = f"rate_limit:{client_ip}:{current_window}"
    await redis_client.delete(key)

    # Instead of sending 1000 requests (slow), we manually set the counter
    # just below the limit, then exhaust it.
    limit = settings.RATE_LIMIT_IP
    await redis_client.set(key, limit)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Send 101st request - should fail (since we set it to limit)
        # Wait, if we set it to limit, the NEXT request increments it to limit+1
        # and fails?
        # Let's check logic:
        # request_count = await redis.incr(key)
        # if request_count > self.ip_limit: fail

        # So if we set to limit, incr becomes limit+1, which is > limit. So it fails.

        response = await ac.get("/this-does-not-exist")
        assert response.status_code == 429
        assert "Too Many Requests" in response.json()["error"]

        # 2. Verify /health/ is NOT blocked even when limit is exceeded
        health_response = await ac.get("/health/")
        assert health_response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limiter_recovery(redis_client: Redis, app: FastAPI) -> None:
    """
    Test that the rate limiter allows requests again after the window passes.
    """
    client_ip = "127.0.0.1"
    current_window = int(time.time() // 60)
    key = f"rate_limit:{client_ip}:{current_window}"

    # Exhaust limit manually
    await redis_client.set(key, settings.RATE_LIMIT_IP + 10)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Verify blocked
        response = await ac.get("/this-does-not-exist")
        assert response.status_code == 429

        # 2. Reset (simulate time passing)
        # We delete keys for current and adjacent windows to be safe
        for w in [current_window, current_window - 1, current_window + 1]:
            key = f"rate_limit:127.0.0.1:{w}"
            await redis_client.delete(key)

        # 3. Verify recovery
        response = await ac.get("/this-does-not-exist")
        assert response.status_code != 429
