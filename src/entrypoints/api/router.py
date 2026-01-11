from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dependencies import (
    get_db_session,
    get_graph,
    get_memory_service,
    get_sphere_repository,
)
from src.domain.ports.memory_service import MemoryServiceProtocol
from src.domain.ports.sphere_repository import SphereRepositoryProtocol
from src.entrypoints.api.schemas import ChatRequest, ChatResponse, ThreadStateResponse
from src.infra.security.content_safety import contains_profanity

router = APIRouter(prefix="/v1/chat")


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    graph: Any = Depends(get_graph),  # noqa: B008
    db: AsyncSession = Depends(get_db_session),  # noqa: B008
    memory: MemoryServiceProtocol = Depends(get_memory_service),  # noqa: B008
    sphere_repo: SphereRepositoryProtocol = Depends(get_sphere_repository),  # noqa: B008
) -> ChatResponse:
    """
    Main entrypoint for the agent chat.
    """
    if contains_profanity(request.message):
        raise HTTPException(
            status_code=400, detail="Message contains inappropriate content."
        )

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

    return ChatResponse.from_state(final_state)


@router.get("/debug/state/{thread_id}", response_model=ThreadStateResponse)
async def get_state(
    thread_id: str,
    graph: Any = Depends(get_graph),  # noqa: B008
) -> ThreadStateResponse:
    """
    Returns the current state of a thread.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state_snapshot = await graph.aget_state(config)
    if not state_snapshot.values:
        from src.domain.exceptions import ResourceNotFound

        raise ResourceNotFound(f"Thread '{thread_id}' not found.")

    # Convert internal state to public DTO
    return ThreadStateResponse(**state_snapshot.values)
