from unittest.mock import AsyncMock, patch

import pytest

from src.app.graph.workflow import create_graph
from src.app.schemas import CritiqueSchema, PlanSchema, PlanStep


@pytest.mark.asyncio
async def test_graph_initialization():
    app = create_graph()
    assert app is not None


@pytest.mark.asyncio
async def test_graph_execution_flow():
    app = create_graph()

    # Initial State
    initial_state = {
        "messages": [{"role": "user", "content": "Hi there"}],
        "user_id": "test_user",
        "step_count": 0,
        "error_count": 0,
        "last_agent": "start",
        "plan": None,
        "critique": None,  # Added to match AgentState
        "plan_approved": True,  # Skip approval for this test
    }

    # config is required for checkpointer
    config = {"configurable": {"thread_id": "test_thread"}}

    # Mock all LLM clients used in the nodes
    with (
        patch("src.app.graph.nodes.architect.llm_client") as mock_arch,
        patch("src.app.graph.nodes.critic.llm_client") as mock_critic,
        patch("src.app.graph.nodes.interviewer.llm_client") as mock_inter,
    ):
        # Setup mocks
        mock_arch.generate = AsyncMock(
            return_value=PlanSchema(
                goal_analysis="User says hi",
                steps=[PlanStep(id=1, description="Greet back")],
                missing_info=[],
            )
        )
        mock_critic.generate = AsyncMock(
            return_value=CritiqueSchema(
                is_approved=True, feedback="Good plan", score=10
            )
        )
        mock_inter.generate_text = AsyncMock(
            return_value="Hello! I am your interviewer."
        )

        # Run the graph
        final_state = await app.ainvoke(initial_state, config=config)

    # Verify the flow: update step count, last agent
    assert final_state["step_count"] > 0
    assert final_state["last_agent"] == "interviewer"

    last_msg = final_state["messages"][-1]
    # Handle both raw dicts and LangGraph message objects
    if isinstance(last_msg, dict):
        assert last_msg["role"] == "assistant"
    else:
        assert last_msg.type == "ai"
