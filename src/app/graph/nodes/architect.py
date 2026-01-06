from typing import Any

from src.app.graph.state import AgentState
from src.app.schemas import PlanSchema
from src.infra.llm.client import get_llm_client

llm_client = get_llm_client()


async def architect_node(state: AgentState) -> dict[str, Any]:
    """
    Analyzes conversation and updates the Plan.
    """
    messages = state["messages"]

    plan = await llm_client.generate(
        system_prompt="You are the Architect...",
        messages=messages,
        schema=PlanSchema,
    )

    return {
        "plan": plan,
        "last_agent": "architect",
        "step_count": state["step_count"] + 1,
    }
