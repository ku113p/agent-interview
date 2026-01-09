from typing import Protocol
from uuid import UUID

from src.domain.entities.sphere import Sphere


class SphereRepositoryProtocol(Protocol):
    """Interface for Sphere persistence and management."""

    async def get_by_id(self, sphere_id: UUID) -> Sphere | None:
        """Fetch sphere by ID."""
        ...

    async def get_by_user_id(self, user_id: UUID) -> list[Sphere]:
        """Get all spheres for a user."""
        ...

    async def save(self, sphere: Sphere) -> None:
        """Persist sphere state."""
        ...

    async def delete(self, sphere_id: UUID) -> None:
        """Delete a sphere."""
        ...
