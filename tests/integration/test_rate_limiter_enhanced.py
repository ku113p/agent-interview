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
async def test_user_rate_limit_enforcement(redis_client: Redis, app: FastAPI) -> None:
    """
    Test that the rate limiter enforces the user-specific limit (100/min)
    when X-User-ID is present.
    """
    # Clear Redis
    await redis_client.flushall()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        user_id = "test-user-1"
        headers = {"X-User-ID": user_id}

        # 1. Send allowed requests (up to RATE_LIMIT_USER)
        # We'll send a few to verify it works, then simulate hitting the limit
        # manually in Redis to speed up the test
        response = await ac.get("/api/v1/not-found", headers=headers)
        assert response.status_code != 429

        # Manually set the counter to the limit
        current_window = int(time.time() // 60)
        key = f"rate_limit:user:{user_id}:{current_window}"
        await redis_client.set(key, settings.RATE_LIMIT_USER)

        # 2. Next request should fail
        response = await ac.get("/api/v1/not-found", headers=headers)
        assert response.status_code == 429
        assert "Too Many Requests" in response.json()["error"]


@pytest.mark.asyncio
async def test_ip_fallback_enforcement(redis_client: Redis, app: FastAPI) -> None:
    """
    Test that the rate limiter falls back to IP-based limiting (1000/min)
    when X-User-ID is missing.
    """
    await redis_client.flushall()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # No headers

        # Manually set the IP counter to the limit
        # Note: In tests, client.host is often '127.0.0.1' or 'testclient'
        # The middleware gets it from request.client.host
        client_ip = "127.0.0.1"
        current_window = int(time.time() // 60)
        key = f"rate_limit:{client_ip}:{current_window}"

        # Set to USER limit first to prove we can go past it (since IP limit is higher)
        await redis_client.set(key, settings.RATE_LIMIT_USER + 10)

        response = await ac.get("/api/v1/not-found")
        assert response.status_code != 429

        # Now set to IP limit
        await redis_client.set(key, settings.RATE_LIMIT_IP)

        response = await ac.get("/api/v1/not-found")
        assert response.status_code == 429


@pytest.mark.asyncio
async def test_dual_limits_isolation(redis_client: Redis, app: FastAPI) -> None:
    """
    Test that blocking a specific User ID does not block requests from the same IP
    (if they have a different User ID).
    """
    await redis_client.flushall()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        user_blocked = "blocked-user"
        user_active = "active-user"

        # Block the first user naturally
        # Limit is 100. Send 101 requests.
        for _ in range(settings.RATE_LIMIT_USER + 1):
            response = await ac.get(
                "/api/v1/not-found", headers={"X-User-ID": user_blocked}
            )

        # The last one should have been blocked (or the next one)
        # Check current status
        response = await ac.get(
            "/api/v1/not-found", headers={"X-User-ID": user_blocked}
        )
        assert response.status_code == 429

        # Request from active user (same IP)
        response = await ac.get("/api/v1/not-found", headers={"X-User-ID": user_active})
        assert response.status_code != 429
