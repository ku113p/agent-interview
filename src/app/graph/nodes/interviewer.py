from typing import Any

from src.app.graph.state import AgentState
from src.infra.llm.client import SimulatedOpenAIClient

llm_client = SimulatedOpenAIClient()


async def interviewer_node(state: AgentState) -> dict[str, Any]:
    """
    Generates the next response to the user.
    """
    messages = state["messages"]

    response_text = await llm_client.generate_text(
        system_prompt="You are the Interviewer...",
        messages=messages
    )

    return {
        "messages": [{"role": "assistant", "content": response_text}],
        "last_agent": "interviewer",
        "step_count": state["step_count"] + 1,
    }
