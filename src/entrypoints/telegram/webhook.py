from typing import Any

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from src.app.dependencies import get_graph
from src.entrypoints.telegram.client import TelegramClient
from src.infra.security.sanitization import sanitize_input
from src.settings import settings

logger = structlog.get_logger()
router = APIRouter(prefix="/telegram")


async def _process_approval_action(
    graph: Any, thread_id: str, plan_approved: bool
) -> str:
    """Process plan approval action and run graph."""
    config = {"configurable": {"thread_id": thread_id}}
    current_state = await graph.aget_state(config)

    if not current_state.values:
        return "Error: No active conversation found."

    # Update state
    updated_state = current_state.values.copy()
    updated_state["plan_approved"] = plan_approved
    updated_state["messages"] = updated_state.get("messages", []) + [
        {
            "role": "user",
            "content": f"Plan {'approved' if plan_approved else 'rejected'}",
        }
    ]

    # Continue graph
    final_state = await graph.ainvoke(updated_state, config=config)
    messages = final_state.get("messages", [])

    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, dict):
            return str(last_msg.get("content", ""))
        elif hasattr(last_msg, "content"):
            return str(last_msg.content)

    return "Plan processed."


async def _handle_callback_query(
    callback_query: dict[str, Any], graph: Any, client: TelegramClient
) -> None:
    """Handle button presses for plan approval."""
    query_id = callback_query.get("id")
    chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
    user_id = callback_query.get("from", {}).get("id")
    data = callback_query.get("data")

    if not query_id or not chat_id or not user_id or not data:
        logger.warning("callback_query_missing_data", callback_query=callback_query)
        return

    thread_id = f"telegram_{user_id}"

    try:
        await client.answer_callback_query(query_id)
        response_text = await _process_approval_action(
            graph, thread_id, data == "approve"
        )
        await client.send_message(chat_id, response_text)

    except Exception as e:
        logger.exception("callback_query_processing_error", error=str(e))


async def _process_chat_message(
    graph: Any, thread_id: str, user_id: int, text: str
) -> tuple[str, dict[str, Any] | None]:
    """Run graph for chat message and return response text and markup."""
    input_state = {
        "messages": [{"role": "user", "content": text}],
        "user_id": str(user_id),
        "step_count": 0,
        "error_count": 0,
        "last_agent": "start",
        "plan": None,
        "plan_approved": None,
        "summary": "",
        "critique": None,
        "current_sphere_id": None,
    }
    config = {"configurable": {"thread_id": thread_id}}

    final_state = await graph.ainvoke(input_state, config=config)
    messages = final_state.get("messages", [])
    response_text = "I'm having trouble thinking of a response."

    if messages:
        last_msg = messages[-1]
        content = ""
        if isinstance(last_msg, dict):
            content = last_msg.get("content", "")
        elif hasattr(last_msg, "content"):
            content = last_msg.content
        if content:
            response_text = str(content)

    reply_markup = None
    if "Would you like to proceed with this plan" in response_text:
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "✅ Approve", "callback_data": "approve"},
                    {"text": "❌ Reject", "callback_data": "reject"},
                ]
            ]
        }

    return response_text, reply_markup


async def process_telegram_update(data: dict[str, Any], graph: Any) -> None:
    """
    Background task to process the telegram update and send a response.
    """
    client = TelegramClient(settings.TELEGRAM_BOT_TOKEN)

    try:
        callback_query = data.get("callback_query")
        if callback_query:
            await _handle_callback_query(callback_query, graph, client)
            return

        message = data.get("message")
        if not message:
            logger.warning("telegram_update_no_message", data=data)
            return

        chat_id = message.get("chat", {}).get("id")
        user_id = message.get("from", {}).get("id")
        text = message.get("text")

        if not chat_id or not text:
            logger.info("telegram_update_ignored_no_text", chat_id=chat_id)
            return

        text = sanitize_input(text)

        thread_id = f"telegram_{user_id}"
        logger.info(
            "processing_telegram_message",
            chat_id=chat_id,
            user_id=user_id,
            thread_id=thread_id,
        )

        response_text, reply_markup = await _process_chat_message(
            graph, thread_id, user_id, text
        )
        await client.send_message(chat_id, response_text, reply_markup=reply_markup)

    except Exception as e:
        logger.exception("telegram_processing_error", error=str(e))
    finally:
        await client.close()


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    graph: Any = Depends(get_graph),  # noqa: B008
) -> dict[str, str]:
    """
    Receives updates from Telegram.
    Returns 200 OK immediately to satisfy Telegram's timeout,
    and processes in background.
    """
    try:
        data = await request.json()

        # Quick validation
        if not data:
            return {"status": "ignored"}

        # Add to background tasks
        background_tasks.add_task(process_telegram_update, data, graph)

        return {"status": "accepted"}
    except Exception as e:
        logger.error("telegram_webhook_error", error=str(e))
        # Even on error, we might want to return 200 to stop Telegram from retrying
        # indefinitely if it's a malformed payload check.
        # But for system errors, 500 is appropriate.
        raise HTTPException(status_code=500, detail="Internal Server Error") from e
