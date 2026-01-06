from typing import Any

from fastapi import Depends, Request

from src.domain.ports.memory_service import MemoryServiceProtocol
from src.infra.db.session import get_db_session
from src.infra.redis import get_redis_client
from src.infra.vector.memory import RedisMemoryService


def get_graph(request: Request) -> Any:
    """
    Retrieves the initialized LangGraph runnable from the app state.
    """
    if not hasattr(request.app.state, "graph"):
        raise RuntimeError("Graph has not been initialized in app state.")
    return request.app.state.graph


def get_memory_service(
    redis=Depends(get_redis_client),
) -> MemoryServiceProtocol:
    """
    Dependency that provides an initialized MemoryService.
    """
    return RedisMemoryService(redis)


__all__ = ["get_graph", "get_db_session", "get_memory_service", "get_redis_client"]
