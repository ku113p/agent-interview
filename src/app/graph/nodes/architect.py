import json
from typing import Any

from src.app.graph.state import AgentState
from src.app.prompts.renderer import render_prompt
from src.app.schemas import PlanSchema
from src.infra.llm.client import get_llm_client

llm_client = get_llm_client()


async def architect_node(state: AgentState) -> dict[str, Any]:
    """
    Analyzes conversation and updates the Plan.
    """
    messages = state["messages"]

    user_profile = state.get("user_profile")
    up_data: dict[str, Any]
    if user_profile is not None and hasattr(user_profile, "model_dump"):
        up_data = user_profile.model_dump()
    elif isinstance(user_profile, dict):
        up_data = user_profile
    else:
        up_data = {}

    # Extract user request from last message
    if messages:
        last_msg = messages[-1]
        user_request = (
            last_msg.content
            if hasattr(last_msg, "content")
            else str(last_msg)
        )
    else:
        user_request = ""

    system_prompt = render_prompt(
        "architect.j2",
        user_profile_json=json.dumps(up_data),
        user_request=user_request,
    )

    plan = await llm_client.generate(
        system_prompt=system_prompt,
        messages=messages,
        schema=PlanSchema,
    )

    return {
        "plan": plan,
        "last_agent": "architect",
        "step_count": state["step_count"] + 1,
    }
