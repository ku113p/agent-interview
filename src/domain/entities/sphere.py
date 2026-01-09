from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class SphereStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Sphere(BaseModel):
    """
    Domain entity representing a biography topic/sphere.

    A Sphere is a focused area of biography collection (e.g., "Career", "Childhood").
    Each user can have multiple spheres with different statuses.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4, description="Unique sphere ID")
    user_id: UUID = Field(description="Owner of this sphere")

    name: str = Field(min_length=1, description="Sphere name, e.g., 'Career 2010-2015'")
    description: str | None = Field(
        default=None, description="Optional description of the sphere"
    )

    status: SphereStatus = Field(
        default=SphereStatus.NOT_STARTED, description="Current collection status"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def start_session(self) -> "Sphere":
        """Mark sphere as in progress when starting a session."""
        if self.status == SphereStatus.COMPLETED:
            raise ValueError("Cannot start session on completed sphere")
        return self.model_copy(update={"status": SphereStatus.IN_PROGRESS})

    def complete(self) -> "Sphere":
        """Mark sphere as completed."""
        return self.model_copy(update={"status": SphereStatus.COMPLETED})
