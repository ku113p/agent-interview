import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis

from src.main import create_app


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.mark.asyncio
async def test_budget_exceeded(redis_client: Redis, app: FastAPI) -> None:
    """
    Test that requests are blocked when the user's token budget is exceeded.
    """
    await redis_client.flushall()

    user_id = "budget-user"
    base_key = f"usage:user:{user_id}"

    # Set usage to exceed limit
    # Limit is 100,000. Let's set inputs to 50,000 and outputs to 50,001
    await redis_client.set(f"{base_key}:input_tokens", 50000)
    await redis_client.set(f"{base_key}:output_tokens", 50001)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-ID": user_id}

        # Should be blocked - using a dummy endpoint to ensure we hit middleware
        # even if we used /v1/chat/message before, hitting a 404 endpoint is safer
        # to avoid app logic execution
        response = await ac.get("/api/v1/not-found", headers=headers)

        assert response.status_code == 429
        # Check the 'error' field, not 'message'
        assert "Budget Exceeded" in response.json()["error"]


@pytest.mark.asyncio
async def test_budget_within_limit(redis_client: Redis, app: FastAPI) -> None:
    """
    Test that requests are allowed when within budget.
    """
    await redis_client.flushall()

    user_id = "rich-user"
    base_key = f"usage:user:{user_id}"

    await redis_client.set(f"{base_key}:input_tokens", 100)
    await redis_client.set(f"{base_key}:output_tokens", 100)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {"X-User-ID": user_id}

        # We use a 404 endpoint.
        # If budget is OK, it proceeds to router -> 404.
        # If budget exceeded, middleware returns 429.

        response = await ac.get("/api/v1/not-found", headers=headers)

        assert response.status_code != 429
        assert response.status_code == 404
