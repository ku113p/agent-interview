from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class MemoryKind(str, Enum):
    SEMANTIC = "semantic"  # General knowledge / skills
    EPISODIC = "episodic"  # Specific events from conversation
    FACTUAL = "factual"  # Hard facts about the user (e.g. Name, Age)


class MemoryFragment(BaseModel):
    """
    Value Object representing a discrete piece of information.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    content: str
    kind: MemoryKind

    # Metadata for search relevance
    importance: int = Field(default=1, ge=1, le=10)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Link back to user, but strictly via ID (Decoupling)
    user_id: UUID

    def mark_important(self) -> "MemoryFragment":
        """Promotes memory importance."""
        return self.model_copy(update={"importance": 10})
