from typing import Any, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.domain.exceptions import LLMMessageValidationError

Role = Literal["system", "user", "assistant", "tool"]
VALID_ROLES: set[Role] = {"system", "user", "assistant", "tool"}


class OpenAIMessage(TypedDict):
    role: str
    content: str


def convert_to_openai_messages(messages: list[Any]) -> list[OpenAIMessage]:
    """
    Converts a list of messages to the OpenAI dictionary format with strict validation.

    Supported formats:
    1. Dictionaries with 'role' and 'content' keys.
       - 'role' must be one of: 'system', 'user', 'assistant', 'tool'.
    2. LangChain BaseMessage objects (HumanMessage, AIMessage, SystemMessage).
    3. Objects with 'content' and 'type' attributes
       (duck typing for LangChain messages).

    Raises:
        LLMMessageValidationError:
            If a message cannot be converted or has an invalid role.
    """
    formatted: list[OpenAIMessage] = []

    for i, msg in enumerate(messages):
        try:
            if isinstance(msg, dict):
                formatted.append(_validate_dict_message(msg))
            elif isinstance(msg, BaseMessage) or (
                hasattr(msg, "content") and hasattr(msg, "type")
            ):
                formatted.append(_convert_object_message(msg))
            else:
                raise LLMMessageValidationError(
                    f"Message at index {i} has unsupported type: {type(msg)}. "
                    "Expected dict or LangChain Message object."
                )
        except LLMMessageValidationError as e:
            # Re-raise with index context if not present
            if f"at index {i}" not in str(e):
                raise LLMMessageValidationError(
                    f"Invalid message at index {i}: {e}"
                ) from e
            raise e

    return formatted


def _validate_dict_message(msg: dict[str, Any]) -> OpenAIMessage:
    if "role" not in msg:
        raise LLMMessageValidationError(
            "Missing required key 'role' in dictionary message."
        )
    if "content" not in msg:
        raise LLMMessageValidationError(
            "Missing required key 'content' in dictionary message."
        )

    role = str(msg["role"]).lower()
    if role not in VALID_ROLES:
        raise LLMMessageValidationError(
            f"Invalid role '{role}'. Must be one of: {', '.join(sorted(VALID_ROLES))}"
        )

    return {"role": role, "content": str(msg["content"])}


def _convert_object_message(msg: Any) -> OpenAIMessage:
    content = str(msg.content)

    # Handle explicit LangChain types
    if isinstance(msg, HumanMessage):
        return {"role": "user", "content": content}
    if isinstance(msg, AIMessage):
        return {"role": "assistant", "content": content}
    if isinstance(msg, SystemMessage):
        return {"role": "system", "content": content}

    # Handle generic/duck-typed messages (e.g. BaseMessage with type string)
    msg_type = getattr(msg, "type", "unknown")

    role_map = {
        "human": "user",
        "user": "user",
        "ai": "assistant",
        "assistant": "assistant",
        "system": "system",
        "tool": "tool",
        "chat": "user",  # Common fallback in LangChain for generic chat messages
    }

    if msg_type in role_map:
        return {"role": role_map[msg_type], "content": content}

    raise LLMMessageValidationError(
        f"Could not map message type '{msg_type}' to a valid OpenAI role."
    )


# --- Legacy Helpers (kept for backward compatibility with other modules) ---


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

    # Reuse the logic from conversion but without validation raising
    try:
        if isinstance(message, BaseMessage) or (
            hasattr(message, "content") and hasattr(message, "type")
        ):
            return _convert_object_message(message)["role"]
    except LLMMessageValidationError:
        pass

    if hasattr(message, "type"):
        return str(message.type)

    return "unknown"
