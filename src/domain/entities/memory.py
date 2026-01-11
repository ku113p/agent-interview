from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class MemoryKind(str, Enum):
    SEMANTIC = "semantic"  # General knowledge / facts
    EPISODIC = "episodic"  # Specific events
    FACTUAL = "factual"  # Hard data points (e.g., "Born in 1990")


class MemoryFragment(BaseModel):
    """
    Atomic unit of memory.
    Represents a single fact or interaction stored in the Vector DB (Mem0).
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4, description="Unique memory ID")
    user_id: UUID = Field(description="Owner of this memory")

    content: str = Field(min_length=1, description="The actual text content")
    kind: MemoryKind = Field(default=MemoryKind.SEMANTIC)

    importance: int = Field(default=1, ge=1, le=10, description="1-10 relevance score")

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str] = Field(default_factory=dict)

    def mark_important(self) -> "MemoryFragment":
        """
        Mark memory as critically important (score 10).
        Returns a new instance.
        """
        return self.model_copy(update={"importance": 10})
