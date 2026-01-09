from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages

from src.app.schemas import PlanSchema


class AgentState(TypedDict):
    """
    Global state for the Agentic Workflow.
    """

    messages: Annotated[list[dict[str, Any]], add_messages]

    user_id: str
    current_sphere_id: str | None
    plan: PlanSchema | None
    critique: Any | None
    plan_approved: bool | None  # None = pending, True = approved, False = rejected

    step_count: int
    error_count: int
    last_agent: str
