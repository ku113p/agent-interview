from uuid import UUID

from mem0 import Memory  # type: ignore

from src.domain.entities.memory import MemoryFragment, MemoryKind
from src.domain.ports.memory_service import MemoryServiceProtocol


class Mem0MemoryService(MemoryServiceProtocol):
    """
    Implementation of MemoryService using Mem0 with Qdrant vector store.

    Mem0 handles semantic search, importance scoring, and memory consolidation.
    """

    def __init__(self, qdrant_host: str = "localhost", qdrant_port: int = 6333):
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "host": qdrant_host,
                    "port": qdrant_port,
                },
            }
        }
        self._memory = Memory.from_config(config)

    async def add(self, fragment: MemoryFragment) -> None:
        """
        Store memory fragment in Mem0.

        Mem0 expects messages in a specific format for conversations.
        We'll store as a single message with metadata.
        """
        # Convert to Mem0 format
        # Mem0 expects a list of messages, but for single fragments we can pass one
        messages = [
            {
                "role": "user",  # Treat as user input for now
                "content": fragment.content,
            }
        ]

        # Mem0 metadata can include our custom fields
        metadata = {
            "kind": fragment.kind.value,
            "importance": fragment.importance,
            "created_at": fragment.created_at.isoformat(),
            "fragment_id": str(fragment.id),
        }

        # Add to memory with user_id for isolation
        self._memory.add(messages, user_id=str(fragment.user_id), metadata=metadata)

    async def search(
        self, query: str, user_id: UUID, kind: MemoryKind | None = None, limit: int = 5
    ) -> list[MemoryFragment]:
        """
        Semantic search using Mem0.

        Mem0 returns memories with relevance scores.
        """
        # Mem0 search returns list of dicts with 'memory', 'score', 'id', etc.
        results = self._memory.search(query, user_id=str(user_id), limit=limit)

        fragments = []
        for result in results:
            # Mem0 returns memories in various formats, need to parse
            if isinstance(result, dict):
                memory_data = result.get("memory", "")
                metadata_raw = result.get("metadata", {})
            elif isinstance(result, str):
                memory_data = result
                metadata_raw = {}
            else:
                continue

            # Ensure metadata is a dict
            metadata = metadata_raw if isinstance(metadata_raw, dict) else {}

            # Reconstruct MemoryFragment
            try:
                fragment_id_str = metadata.get("fragment_id", "")
                kind_str = metadata.get("kind", "semantic")
                importance_str = metadata.get("importance", "1")
                created_at_str = metadata.get("created_at", "")

                fragment = MemoryFragment(
                    id=UUID(fragment_id_str) if fragment_id_str else UUID(),
                    content=str(memory_data),
                    kind=MemoryKind(kind_str),
                    importance=int(importance_str),
                    user_id=user_id,
                    created_at=created_at_str,  # This will be parsed by Pydantic
                )
                fragments.append(fragment)
            except (ValueError, KeyError, TypeError):
                # Skip malformed memories
                continue

        return fragments

    async def get_recent(self, user_id: UUID, limit: int = 10) -> list[MemoryFragment]:
        """
        Get recent memories.

        Mem0 doesn't have a direct "recent" API, so we'll use search with empty query
        or implement a fallback.
        """
        # For recent memories, we can search with a broad query or use history
        # For now, use a dummy query to get recent memories
        return await self.search("", user_id, limit=limit)
