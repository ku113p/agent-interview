from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmailAddress(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: str

    @field_validator("value")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v_lower = v.lower()
        if "tempmail" in v_lower:
            raise ValueError("Disposable emails are forbidden.")
        return v_lower

    def __str__(self) -> str:
        return self.value


class Profession(BaseModel):
    model_config = ConfigDict(frozen=True)
    title: str
    experience_years: int = Field(ge=0)


Role = Literal["system", "user", "assistant", "tool"]


class Message(BaseModel):
    """
    Domain representation of a message.
    Decoupled from infrastructure (LangChain/OpenAI).
    """

    role: Role
    content: str
    model_config = ConfigDict(frozen=True)
