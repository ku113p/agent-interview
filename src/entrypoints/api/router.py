from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.app.dependencies import get_graph

router = APIRouter(prefix="/v1/chat")


class ChatRequest(BaseModel):
    user_id: str
    message: str
    thread_id: str = "default_thread"


class ChatResponse(BaseModel):
    response: str
    step_count: int


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    graph: Any = Depends(get_graph),  # noqa: B008
) -> ChatResponse:
    """
    Main entrypoint for the agent chat.
    """
    input_state = {
        "messages": [{"role": "user", "content": request.message}],
        "user_id": request.user_id,
        "step_count": 0,
        "error_count": 0,
        "last_agent": "start",
        "plan": None,
    }

    config = {"configurable": {"thread_id": request.thread_id}}

    try:
        final_state = await graph.ainvoke(input_state, config=config)

        messages = final_state.get("messages", [])
        if not messages:
            return ChatResponse(
                response="No response generated.",
                step_count=final_state.get("step_count", 0),
            )

        last_msg = messages[-1]
        content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

        if isinstance(last_msg, dict):
            content = last_msg.get("content", "")

        return ChatResponse(
            response=str(content), step_count=final_state.get("step_count", 0)
        )

    except Exception as e:
        import structlog

        logger = structlog.get_logger()
        logger.exception("chat_message_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/debug/state/{thread_id}")
async def get_state(
    thread_id: str,
    graph: Any = Depends(get_graph),  # noqa: B008
) -> dict[str, Any]:
    """
    Returns the current state of a thread.
    """
    config = {"configurable": {"thread_id": thread_id}}
    try:
        # Get the current state snapshot
        state_snapshot = await graph.aget_state(config)
        return dict(state_snapshot.values)
    except Exception as e:
        raise HTTPException(
            status_code=404, detail=f"Thread not found or error: {str(e)}"
        ) from e
