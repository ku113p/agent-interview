from typing import Any

from langchain_core.runnables import RunnableConfig
from langfuse import observe

from src.app.graph.state import AgentState
from src.app.prompts.renderer import render_prompt
from src.infra.llm.client import get_llm_client

llm_client = get_llm_client()


@observe()
async def interviewer_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """
    Generates the next response to the user.
    """
    configurable = config.get("configurable", {})
    _ = configurable.get("db_session")
    _ = configurable.get("memory_service")
    messages = state["messages"]

    system_prompt = render_prompt(
        "interviewer.j2", context=str(state.get("plan", "No plan established yet."))
    )

    response_text = await llm_client.generate_text(
        system_prompt=system_prompt, messages=messages
    )

    return {
        "messages": [{"role": "assistant", "content": response_text}],
        "last_agent": "interviewer",
        "step_count": state["step_count"] + 1,
    }
