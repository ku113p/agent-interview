from typing import Any

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from src.app.dependencies import get_graph
from src.entrypoints.telegram.client import TelegramClient
from src.settings import settings

logger = structlog.get_logger()
router = APIRouter(prefix="/telegram")


async def process_telegram_update(data: dict[str, Any], graph: Any) -> None:
    """
    Background task to process the telegram update and send a response.
    """
    client = TelegramClient(settings.TELEGRAM_BOT_TOKEN)

    try:
        # Extract message info
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

        # Map Telegram user to internal thread
        # We prefix with 'telegram_' to avoid collision with other sources
        thread_id = f"telegram_{user_id}"

        logger.info(
            "processing_telegram_message",
            chat_id=chat_id,
            user_id=user_id,
            thread_id=thread_id,
        )

        # Prepare graph input
        input_state = {
            "messages": [{"role": "user", "content": text}],
            "user_id": str(user_id),
            "step_count": 0,
            "error_count": 0,
            "last_agent": "start",
            "plan": None,
        }

        config = {"configurable": {"thread_id": thread_id}}

        # Invoke graph
        # Note: In a real prod scenario, we might want to offload this to a worker queue
        # (Celery/Arq) because Telegram has a timeout for webhooks. 
        # For now, BackgroundTasks is a good middle ground.
        final_state = await graph.ainvoke(input_state, config=config)

        # Extract response
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

        # Send back to Telegram
        await client.send_message(chat_id, response_text)

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
