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

    # Handle explicit LangChain types
    if isinstance(message, HumanMessage):
        return "user"
    if isinstance(message, AIMessage):
        return "assistant"
    if isinstance(message, SystemMessage):
        return "system"

    # Handle generic/duck-typed messages
    msg_type = getattr(message, "type", "unknown")

    role_map = {
        "human": "user",
        "user": "user",
        "ai": "assistant",
        "assistant": "assistant",
        "system": "system",
        "tool": "tool",
        "chat": "user",
    }

    return role_map.get(msg_type, "unknown")
