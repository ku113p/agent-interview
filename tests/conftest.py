from unittest.mock import AsyncMock, patch

import pytest

from src.app.schemas import CritiqueSchema, PlanSchema


@pytest.fixture(autouse=True)
def mock_llm_safety():
    """
    Global safety fixture to prevent real LLM calls during tests.
    Patches the llm_client in all graph nodes.
    """
    with (
        patch("src.app.graph.nodes.architect.llm_client") as mock_arch,
        patch("src.app.graph.nodes.critic.llm_client") as mock_critic,
        patch("src.app.graph.nodes.interviewer.llm_client") as mock_inter,
    ):
        # Default mock behaviors
        mock_arch.generate = AsyncMock(
            return_value=PlanSchema(
                goal_analysis="Mock analysis", steps=[], missing_info=[]
            )
        )
        mock_critic.generate = AsyncMock(
            return_value=CritiqueSchema(
                is_approved=True, feedback="Global Mock Approved", score=10
            )
        )
        mock_inter.generate_text = AsyncMock(return_value="Global Mock Response")

        yield {"architect": mock_arch, "critic": mock_critic, "interviewer": mock_inter}
