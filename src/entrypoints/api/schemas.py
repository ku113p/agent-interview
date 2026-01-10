from typing import Any

from pydantic import BaseModel, Field

from src.app.schemas import CritiqueSchema, PlanSchema


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    message: str = Field(..., min_length=1, max_length=4096)
    thread_id: str = Field(
        "default_thread", min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$"
    )


class ChatResponse(BaseModel):
    response: str
    step_count: int

    @classmethod
    def from_state(cls, state: dict[str, Any]) -> "ChatResponse":
        messages = state.get("messages", [])
        step_count = state.get("step_count", 0)

        if not messages:
            return cls(response="No response generated.", step_count=step_count)

        last_msg = messages[-1]
        content = ""

        # Handle both dict and object (BaseMessage) formats
        if isinstance(last_msg, dict):
            content = last_msg.get("content", "")
        elif hasattr(last_msg, "content"):
            content = last_msg.content
        else:
            content = str(last_msg)

        return cls(response=str(content), step_count=step_count)


class ThreadStateResponse(BaseModel):
    """
    DTO for the thread state, hiding internal fields like error_count.
    """

    user_id: str
    current_sphere_id: str | None = None
    plan: PlanSchema | None = None
    critique: CritiqueSchema | None = None
    plan_approved: bool | None = None
    step_count: int
    messages: list[dict[str, Any]] = Field(default_factory=list)
