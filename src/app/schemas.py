from typing import Literal

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    id: int
    description: str
    status: Literal["pending", "in_progress", "done"] = "pending"


class PlanSchema(BaseModel):
    """Output for the Architect Agent."""

    goal_analysis: str = Field(description="Understanding of the user's intent")
    steps: list[PlanStep] = Field(description="Sequential steps to achieve the goal")
    missing_info: list[str] = Field(
        default_factory=list, description="Questions to ask the user"
    )


class CritiqueSchema(BaseModel):
    """Output for the Critic Agent."""

    is_approved: bool
    feedback: str
    score: int = Field(ge=0, le=10)
