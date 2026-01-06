from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages

from src.app.schemas import PlanSchema


class AgentState(TypedDict):
    """
    Global state for the Agentic Workflow.
    """

    messages: Annotated[list[dict[str, Any]], add_messages]

    user_id: str
    plan: PlanSchema | None
    critique: Any | None

    step_count: int
    error_count: int
    last_agent: str
