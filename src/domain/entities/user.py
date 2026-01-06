from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserProfile(BaseModel):
    """
    Aggregate Root for the User Context.
    Represents the 'Truth' of the business logic.
    """

    # Immutability prevents implicit state mutation bugs
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID = Field(default_factory=uuid4, description="Unique aggregate ID")
    email: EmailStr
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    full_name: str | None = None

    # Career context
    profession: str | None = None
    experience_years: int = 0

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, v: str) -> str:
        """Domain Logic: We don't accept disposable emails."""
        if "tempmail" in v:
            raise ValueError("Disposable emails are forbidden.")
        return v.lower()

    def activate(self) -> "UserProfile":
        """
        Pure Domain Method.
        Returns a NEW instance (Immutability pattern).
        """
        return self.model_copy(update={"is_active": True})

    def update_profession(self, profession: str, years: int) -> "UserProfile":
        """Updates career information."""
        return self.model_copy(
            update={"profession": profession, "experience_years": years}
        )
