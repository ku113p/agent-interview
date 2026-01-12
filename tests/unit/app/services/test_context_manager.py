from unittest.mock import AsyncMock, Mock

import pytest
from src.domain.value_objects import Message
from src.app.services.context_manager import ContextManager


@pytest.mark.asyncio
async def test_summarize_conversation():
    # Arrange
    mock_llm = Mock()
    mock_llm.generate_text = AsyncMock(return_value="Summary of conversation")

    manager = ContextManager(mock_llm)

    current_summary = "Previous summary"
    messages = [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi there"),
    ]

    # Act
    summary = await manager.summarize_conversation(current_summary, messages)

    # Assert
    assert summary == "Summary of conversation"

    # Verify LLM called with correct prompts
    call_args = mock_llm.generate_text.call_args
    assert call_args
    system_prompt = call_args.kwargs["system_prompt"]
    assert "Previous summary" in system_prompt
    assert "USER: Hello" in system_prompt
    assert "ASSISTANT: Hi there" in system_prompt
