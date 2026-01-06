from collections.abc import AsyncGenerator

from redis.asyncio import Redis as AsyncRedis

from src.settings import settings


async def get_redis_client() -> AsyncGenerator[AsyncRedis, None]:
    """
    Dependency for FastAPI.
    Yields an AsyncRedis client and ensures it's closed after the request.
    """
    client = AsyncRedis.from_url(str(settings.REDIS_URL), decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()
