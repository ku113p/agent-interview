from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dependencies import (
    get_db_session,
    get_graph,
    get_memory_service,
    get_sphere_repository,
)
from src.domain.ports.memory_service import MemoryServiceProtocol
from src.domain.ports.sphere_repository import SphereRepositoryProtocol

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
    db: AsyncSession = Depends(get_db_session),
    memory: MemoryServiceProtocol = Depends(get_memory_service),
    sphere_repo: SphereRepositoryProtocol = Depends(get_sphere_repository),
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
        "plan_approved": None,
    }

    config = {
        "configurable": {
            "thread_id": request.thread_id,
            "db_session": db,
            "memory_service": memory,
            "sphere_repo": sphere_repo,
        }
    }

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


@router.get("/debug/state/{thread_id}")
async def get_state(
    thread_id: str,
    graph: Any = Depends(get_graph),  # noqa: B008
) -> dict[str, Any]:
    """
    Returns the current state of a thread.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state_snapshot = await graph.aget_state(config)
    if not state_snapshot.values:
        from src.domain.exceptions import ResourceNotFound

        raise ResourceNotFound(f"Thread '{thread_id}' not found.")
    return dict(state_snapshot.values)
