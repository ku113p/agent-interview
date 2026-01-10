from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


def get_message_content(message: Any) -> str:
    """Safely extracts content string from various message formats."""
    if isinstance(message, dict):
        return str(message.get("content", ""))

    if hasattr(message, "content"):
        return str(message.content)

    return str(message)


def get_message_role(message: Any) -> str:
    """Safely extracts role string from various message formats."""
    if isinstance(message, dict):
        return str(message.get("role", "unknown"))

    if isinstance(message, HumanMessage):
        return "user"
    if isinstance(message, AIMessage):
        return "assistant"
    if isinstance(message, SystemMessage):
        return "system"

    if hasattr(message, "type"):
        return str(message.type)

    return "unknown"
