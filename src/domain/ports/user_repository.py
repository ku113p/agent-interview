from typing import Protocol
from uuid import UUID

from src.domain.entities.user import UserProfile


class UserRepositoryProtocol(Protocol):
    """Interface for User persistence."""

    async def get_by_id(self, user_id: UUID) -> UserProfile | None:
        """Fetch user or return None."""
        ...

    async def get_by_email(self, email: str) -> UserProfile | None:
        """Fetch user by email."""
        ...

    async def list_all(self, limit: int, offset: int) -> list[UserProfile]:
        """List all users with pagination."""
        ...

    async def save(self, user: UserProfile) -> None:
        """Persist the aggregate state (Upsert)."""
        ...
