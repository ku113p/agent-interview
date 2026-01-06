import pytest

from src.app.schemas import PlanSchema
from src.infra.llm.client import SimulatedOpenAIClient


@pytest.mark.asyncio
async def test_generate_text_returns_string():
    client = SimulatedOpenAIClient()
    response = await client.generate_text("System", [])
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_generate_structured_returns_schema():
    client = SimulatedOpenAIClient()
    # We expect the mock to return an empty/default instance of PlanSchema
    response = await client.generate("System", [], PlanSchema)

    assert isinstance(response, PlanSchema)
    # Since we are using model_construct in the mock, fields might be missing or None
    # if we didn't provide them. For the purpose of the generic Architecture test,
    # verifying the TYPE is what matters for the adapter contract.
