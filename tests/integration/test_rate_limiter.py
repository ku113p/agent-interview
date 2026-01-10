import time

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_rate_limiter_blocks_requests(redis_client):
    """
    Test that the rate limiter blocks requests after the limit is reached.
    We'll assume the limit is 100 per minute as configured in main.py.
    """
    # Use a custom client IP to avoid conflict with other tests

    # We need to monkeypatch the client host retrieval if we were running uvicorn,
    # but with AsyncClient, the 'client' property isn't always set the same way
    # as starlette expects.
    # However, Starlette's Request.client.host usually comes from the scope.
    # AsyncClient allows setting the client tuple in transport, but it's complex.
    # Instead, we rely on the RateLimitMiddleware logic:
    # client_ip = request.client.host if request.client else "unknown"
    # ASGITransport usually sets client to ("127.0.0.1", port)

    # Let's clear any existing rate limit for this IP
    current_window = int(time.time() // 60)
    key = f"rate_limit:127.0.0.1:{current_window}"
    await redis_client.delete(key)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Send 100 allowed requests
        for i in range(100):
            response = await ac.get("/health/")
            # /health is whitelisted! We need to hit a non-whitelisted endpoint.
            # /v1/chat/debug/state/someid is a GET endpoint we can use.
            # But it might return 404 (ResourceNotFound), which is fine,
            # as long as it's not 429.
            # Actually, let's use a non-existent endpoint to be safe/fast,
            # Rate limiter runs *before* routing (middleware).
            response = await ac.get("/this-does-not-exist")
            assert response.status_code != 429, f"Request {i + 1} failed with 429"

        # 2. Send 101st request - should fail
        response = await ac.get("/this-does-not-exist")
        assert response.status_code == 429
        assert "Too Many Requests" in response.json()["error"]

        # 3. Verify /health/ is NOT blocked even when limit is exceeded
        health_response = await ac.get("/health/")
        assert health_response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limiter_recovery(redis_client):
    """
    Test that the rate limiter allows requests again after the window passes.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Exhaust limit
        blocked = False
        for _ in range(110):
            response = await ac.get("/this-does-not-exist")
            if response.status_code == 429:
                blocked = True
                break

        assert blocked, "Failed to exhaust rate limit"

        # 2. Reset (simulate time passing)
        # We delete keys for current and adjacent windows to be safe
        # against time boundaries
        current_window = int(time.time() // 60)
        for w in [current_window, current_window - 1, current_window + 1]:
            key = f"rate_limit:127.0.0.1:{w}"
            await redis_client.delete(key)

        # 3. Verify recovery
        response = await ac.get("/this-does-not-exist")
        assert response.status_code != 429
