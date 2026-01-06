import json
from uuid import UUID

from redis.asyncio import Redis as AsyncRedis

from src.domain.entities.memory import MemoryFragment, MemoryKind
from src.domain.ports.memory_service import MemoryServiceProtocol


class RedisMemoryService(MemoryServiceProtocol):
    """Implementation of MemoryService using Redis."""

    def __init__(self, redis: AsyncRedis):
        self._redis = redis

    async def add(self, fragment: MemoryFragment) -> None:
        """Stores memory in a Redis list for the user."""
        key = f"user:{fragment.user_id}:memories"
        data = fragment.model_dump_json()
        await self._redis.lpush(key, data)  # type: ignore

    async def search(
        self, query: str, user_id: UUID, kind: MemoryKind | None = None, limit: int = 5
    ) -> list[MemoryFragment]:
        """Mock semantic search."""
        return await self.get_recent(user_id, limit)

    async def get_recent(self, user_id: UUID, limit: int = 10) -> list[MemoryFragment]:
        key = f"user:{user_id}:memories"
        items = await self._redis.lrange(key, 0, limit - 1)  # type: ignore

        fragments = []
        for item in items:
            try:
                # item is bytes or str
                if isinstance(item, bytes):
                    item = item.decode("utf-8")

                obj = json.loads(item)
                fragments.append(MemoryFragment(**obj))
            except Exception:
                continue

        return fragments
