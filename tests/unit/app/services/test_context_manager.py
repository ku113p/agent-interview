from unittest.mock import AsyncMock, Mock

import pytest

from src.app.services.context_manager import ContextManager
from src.domain.value_objects import Message


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
        Message(role="user", content="My name is John"),
    ]

    # Act
    summary = await manager.summarize_conversation(current_summary, messages)

    # Assert
    assert summary == "Summary of conversation"
    mock_llm.generate_text.assert_called_once()

    call_args = mock_llm.generate_text.call_args
    system_prompt = call_args.kwargs["system_prompt"]

    assert "USER: Hello" in system_prompt
    assert "ASSISTANT: Hi there" in system_prompt
    assert "USER: My name is John" in system_prompt
