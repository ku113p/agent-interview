from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class EmailAddress(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: EmailStr

    @field_validator("value")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """Domain Logic: We don't accept disposable emails."""
        v_lower = v.lower()
        if "tempmail" in v_lower:
            raise ValueError("Disposable emails are forbidden.")
        return v_lower

    def __str__(self) -> str:
        return self.value


class Career(BaseModel):
    model_config = ConfigDict(frozen=True)
    profession: str
    experience_years: int = 0


class UserProfile(BaseModel):
    """
    Aggregate Root for the User Context.
    Represents the 'Truth' of the business logic.
    """

    # Immutability prevents implicit state mutation bugs
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID = Field(default_factory=uuid4, description="Unique aggregate ID")
    email: EmailAddress
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    full_name: str | None = None

    # Career context
    career: Career | None = None

    @property
    def profession(self) -> str | None:
        return self.career.profession if self.career else None

    @property
    def experience_years(self) -> int:
        return self.career.experience_years if self.career else 0

    def activate(self) -> "UserProfile":
        """
        Pure Domain Method.
        Returns a NEW instance (Immutability pattern).
        """
        return self.model_copy(update={"is_active": True})

    def update_profession(self, profession: str, years: int) -> "UserProfile":
        """Updates career information."""
        new_career = Career(profession=profession, experience_years=years)
        return self.model_copy(update={"career": new_career})
