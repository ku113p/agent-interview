import pytest


@pytest.mark.asyncio
async def test_redis_connection(redis_client):
    """Verify we can connect to Redis and perform basic operations."""
    # Ping
    assert await redis_client.ping() is True

    # Set/Get
    key = "integration_test_key"
    value = "hello_redis"

    await redis_client.set(key, value)
    retrieved = await redis_client.get(key)

    assert retrieved == value

    # Delete
    await redis_client.delete(key)
    assert await redis_client.get(key) is None
