from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.ports.memory_service import MemoryServiceProtocol
from src.domain.ports.sphere_repository import SphereRepositoryProtocol
from src.infra.db.repositories.sphere_repo import SqlAlchemySphereRepository
from src.infra.db.session import get_db_session
from src.infra.mem0.client import Mem0MemoryService
from src.infra.redis import get_redis_client


def get_graph(request: Request) -> Any:
    """
    Retrieves the initialized LangGraph runnable from the app state.
    """
    if not hasattr(request.app.state, "graph"):
        raise RuntimeError("Graph has not been initialized in app state.")
    return request.app.state.graph


def get_memory_service() -> MemoryServiceProtocol:
    """
    Dependency that provides an initialized Mem0MemoryService.
    """
    return Mem0MemoryService()


def get_sphere_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SphereRepositoryProtocol:
    """
    Dependency that provides an initialized SphereRepository.
    """
    return SqlAlchemySphereRepository(session)


__all__ = [
    "get_graph",
    "get_db_session",
    "get_memory_service",
    "get_sphere_repository",
    "get_redis_client",
]
