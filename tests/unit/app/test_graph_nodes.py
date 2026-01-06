from unittest.mock import AsyncMock, patch

import pytest

from src.app.graph.nodes.architect import architect_node
from src.app.graph.nodes.critic import critic_node
from src.app.graph.state import AgentState
from src.app.schemas import CritiqueSchema, PlanSchema, PlanStep


@pytest.fixture
def mock_llm_client():
    return AsyncMock()


@pytest.fixture
def mock_state() -> AgentState:
    return {
        "messages": [{"role": "user", "content": "Build me a website"}],
        "user_id": "test-user",
        "plan": None,
        "critique": None,
        "step_count": 0,
        "error_count": 0,
        "last_agent": "start",
    }


@pytest.fixture
def mock_config():
    return {
        "configurable": {
            "db_session": AsyncMock(),
            "memory_service": AsyncMock(),
            "thread_id": "test-thread",
        }
    }


@pytest.mark.asyncio
async def test_architect_node_generates_plan(mock_state, mock_config):
    # Setup
    with patch("src.app.graph.nodes.architect.llm_client") as mock_client:
        mock_plan = PlanSchema(
            goal_analysis="User wants a website",
            steps=[PlanStep(id=1, description="Init project")],
            missing_info=[],
        )
        mock_client.generate = AsyncMock(return_value=mock_plan)

        # Execute
        result = await architect_node(mock_state, mock_config)

        # Verify
        assert result["last_agent"] == "architect"
        assert result["step_count"] == 1
        assert result["plan"] == mock_plan
        mock_client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_critic_node_generates_critique(mock_state, mock_config):
    # Setup
    with patch("src.app.graph.nodes.critic.llm_client") as mock_client:
        mock_critique = CritiqueSchema(
            is_approved=True, feedback="Looks good", score=10
        )
        mock_client.generate = AsyncMock(return_value=mock_critique)

        # Execute
        result = await critic_node(mock_state, mock_config)

        # Verify
        assert result["last_agent"] == "critic"
        assert result["critique"] == mock_critique
        assert result["step_count"] == 1
        mock_client.generate.assert_called_once()


@pytest.mark.asyncio
async def test_node_receives_dependencies(mock_state, mock_config):
    # Execute
    # We expect these NOT to raise exceptions about missing config keys
    # We need to mock llm_client for architect node as well inside this test scope
    with patch("src.app.graph.nodes.architect.llm_client") as mock_architect_client, \
         patch("src.app.graph.nodes.critic.llm_client") as mock_critic_client:
        
        mock_architect_client.generate = AsyncMock(return_value=PlanSchema(goal_analysis="test", steps=[], missing_info=[]))
        mock_critic_client.generate = AsyncMock(return_value=CritiqueSchema(is_approved=True, feedback="ok", score=10))

        await architect_node(mock_state, mock_config)
        await critic_node(mock_state, mock_config)

    assert True
