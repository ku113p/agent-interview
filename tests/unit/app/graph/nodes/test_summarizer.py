from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import HumanMessage, RemoveMessage

from src.app.graph.nodes.summarizer import (
    SUMMARY_THRESHOLD,
    WINDOW_SIZE,
    summarizer_node,
)
from src.app.graph.state import AgentState


@pytest.mark.asyncio
async def test_summarizer_node_no_action_below_threshold():
    # Arrange
    messages = [
        HumanMessage(content="msg", id=str(i)) for i in range(SUMMARY_THRESHOLD)
    ]
    state = AgentState(messages=messages, summary="", user_id="user1", step_count=0)
    mock_config = {"configurable": {}}

    # Act
    result = await summarizer_node(state, mock_config)

    # Assert
    assert result == {}


@pytest.mark.asyncio
async def test_summarizer_node_actions_above_threshold():
    # Arrange
    # Create messages exceeding threshold
    total_messages = SUMMARY_THRESHOLD + 2
    messages = [
        HumanMessage(content=f"msg{i}", id=str(i)) for i in range(total_messages)
    ]

    state = AgentState(
        messages=messages, summary="Old summary", user_id="user1", step_count=0
    )
    mock_config = {"configurable": {}}

    expected_summary = "New updated summary"

    # Mock ContextManager inside the module
    with patch("src.app.graph.nodes.summarizer.context_manager") as mock_cm:
        mock_cm.summarize_conversation = AsyncMock(return_value=expected_summary)

        # Act
        result = await summarizer_node(state, mock_config)

        # Assert
        assert result["summary"] == expected_summary

        # Check messages to be removed
        # Should remove all except last WINDOW_SIZE
        msgs_to_remove = messages[:-WINDOW_SIZE]
        assert len(result["messages"]) == len(msgs_to_remove)

        for i, remove_msg in enumerate(result["messages"]):
            assert isinstance(remove_msg, RemoveMessage)
            assert remove_msg.id == msgs_to_remove[i].id

        # Verify summarize called with correct messages
        mock_cm.summarize_conversation.assert_called_once()
        call_args = mock_cm.summarize_conversation.call_args
        assert call_args[0][0] == "Old summary"
        assert len(call_args[0][1]) == len(msgs_to_remove)
