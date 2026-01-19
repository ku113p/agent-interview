from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class EmailAddress(BaseModel):
    """
    Value Object representing a valid email address.
    """

    model_config = ConfigDict(frozen=True)

    value: EmailStr = Field(..., description="The email address string")

    @field_validator("value")
    @classmethod
    def validate_domain_rules(cls, v: str) -> str:
        v_lower = v.lower()
        # Domain Rule: No disposable emails
        if "tempmail" in v_lower:
            raise ValueError("Disposable emails are forbidden.")

        return v_lower

    def __str__(self) -> str:
        return self.value


class Message(BaseModel):
    """
    Domain representation of a conversation message.
    """

    model_config = ConfigDict(frozen=True)

    role: str
    content: str
