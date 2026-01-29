from typing import Any

import structlog
from langchain_core.messages import BaseMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig
from langfuse import observe

from src.app.graph.state import AgentState
from src.app.services.context_manager import ContextManager
from src.domain.value_objects import Message
from src.infra.llm.client import get_llm_client
from src.settings import settings

logger = structlog.get_logger()

# Configuration from settings
WINDOW_SIZE = settings.CONVERSATION_WINDOW_SIZE
SUMMARY_THRESHOLD = settings.SUMMARY_THRESHOLD

llm_client = get_llm_client()
context_manager = ContextManager(llm_client)


@observe()
async def summarizer_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    """
    Summarizes older messages and prunes them from the state.
    """
    messages = state["messages"]
    current_summary = state.get("summary", "")

    # If we haven't reached the threshold, do nothing
    if len(messages) <= SUMMARY_THRESHOLD:
        return {}

    # Identify messages to summarize (all except the last WINDOW_SIZE)
    # We always keep the last WINDOW_SIZE messages to maintain immediate context
    msgs_to_summarize = messages[:-WINDOW_SIZE]

    if not msgs_to_summarize:
        return {}

    try:
        # Convert to domain messages
        domain_msgs = []
        for msg in msgs_to_summarize:
            role = "user"
            content = ""

            if isinstance(msg, dict):
                r = msg.get("role", "user")
                content = msg.get("content", "")
                if r in ["system", "user", "assistant", "tool"]:
                    role = r
            elif hasattr(msg, "type"):
                content = getattr(msg, "content", "")
                msg_type = msg.type
                if msg_type == "human":
                    role = "user"
                elif msg_type == "ai":
                    role = "assistant"
                elif msg_type == "system":
                    role = "system"
                elif msg_type == "tool":
                    role = "tool"

            domain_msgs.append(Message(role=role, content=str(content)))

        # Generate new summary
        user_id = state.get("user_id")
        new_summary = await context_manager.summarize_conversation(
            current_summary, domain_msgs, user_id=user_id
        )

        # Create delete operations for summarized messages
        delete_ops = []
        for msg in msgs_to_summarize:
            msg_id = None
            if isinstance(msg, dict):
                msg_id = msg.get("id")
            elif isinstance(msg, BaseMessage):
                msg_id = msg.id
            else:
                msg_id = getattr(msg, "id", None)

            if msg_id:
                delete_ops.append(RemoveMessage(id=msg_id))

        return {
            "summary": new_summary,
            "messages": delete_ops,
        }
    except Exception as e:
        logger.error("summarization_failed", error=str(e))
        # If summarization fails, we return nothing and keep the history as is
        # this prevents data loss or crashing the flow
        return {}
