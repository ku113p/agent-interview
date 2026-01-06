from typing import Protocol
from uuid import UUID

from src.domain.entities.memory import MemoryFragment, MemoryKind


class MemoryServiceProtocol(Protocol):
    """Interface for Semantic Search and Memory Management."""

    async def add(self, fragment: MemoryFragment) -> None:
        """Ingest a new memory fragment."""
        ...

    async def search(
        self, query: str, user_id: UUID, kind: MemoryKind | None = None, limit: int = 5
    ) -> list[MemoryFragment]:
        """Retrieve relevant memories based on semantic similarity."""
        ...

    async def get_recent(self, user_id: UUID, limit: int = 10) -> list[MemoryFragment]:
        """Get latest episodic memories."""
        ...
