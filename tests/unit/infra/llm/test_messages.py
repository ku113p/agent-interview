import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.domain.exceptions import LLMMessageValidationError
from src.infra.llm.messages import convert_to_openai_messages


class TestMessageConversion:
    def test_convert_valid_dicts(self) -> None:
        """Test conversion of valid dictionary messages."""
        messages = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "u"},
            {"role": "assistant", "content": "ai"},
            {"role": "tool", "content": "res"},
        ]
        result = convert_to_openai_messages(messages)
        assert result == messages

    def test_convert_langchain_messages(self) -> None:
        """Test conversion of standard LangChain message objects."""
        messages = [
            SystemMessage(content="sys"),
            HumanMessage(content="u"),
            AIMessage(content="ai"),
        ]
        result = convert_to_openai_messages(messages)
        expected = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "u"},
            {"role": "assistant", "content": "ai"},
        ]
        assert result == expected

    def test_convert_duck_typed_messages(self) -> None:
        """Test conversion of objects mimicking LangChain messages."""

        class MockMsg:
            def __init__(self, content: str, type_: str) -> None:
                self.content = content
                self.type = type_

        messages = [
            MockMsg("u", "human"),
            MockMsg("ai", "ai"),
            MockMsg("sys", "system"),
            MockMsg("generic", "chat"),
            MockMsg("tool_out", "tool"),
        ]
        result = convert_to_openai_messages(messages)
        expected = [
            {"role": "user", "content": "u"},
            {"role": "assistant", "content": "ai"},
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "generic"},
            {"role": "tool", "content": "tool_out"},
        ]
        assert result == expected

    def test_invalid_role_in_dict(self) -> None:
        """Test that invalid roles in dictionaries raise validation error."""
        messages = [{"role": "director", "content": "cut"}]
        with pytest.raises(LLMMessageValidationError) as exc:
            convert_to_openai_messages(messages)
        assert "Invalid role 'director'" in str(exc.value)

    def test_missing_keys_in_dict(self) -> None:
        """Test that missing keys raise validation error."""
        with pytest.raises(LLMMessageValidationError):
            convert_to_openai_messages([{"role": "user"}])  # missing content

        with pytest.raises(LLMMessageValidationError):
            convert_to_openai_messages([{"content": "hi"}])  # missing role

    def test_invalid_types_raise_error(self) -> None:
        """Test that unsupported types (str, int) raise validation error."""
        # This confirms we removed the fallback to str()
        with pytest.raises(LLMMessageValidationError) as exc:
            convert_to_openai_messages(["just a string"])
        assert "unsupported type" in str(exc.value)

        with pytest.raises(LLMMessageValidationError):
            convert_to_openai_messages([123])

    def test_unknown_message_type_attr(self) -> None:
        """Test that objects with unknown 'type' attribute raise error."""

        class UnknownMsg:
            content = "foo"
            type = "alien"

        with pytest.raises(LLMMessageValidationError) as exc:
            convert_to_openai_messages([UnknownMsg()])
        assert "Could not map message type 'alien'" in str(exc.value)
