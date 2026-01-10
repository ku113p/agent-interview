from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.ports.memory_service import MemoryServiceProtocol
from src.domain.ports.sphere_repository import SphereRepositoryProtocol
from src.domain.ports.user_repository import UserRepositoryProtocol
from src.infra.db.repositories.sphere_repo import SqlAlchemySphereRepository
from src.infra.db.repositories.user_repo import SqlAlchemyUserRepository
from src.infra.db.session import get_db_session
from src.infra.mem0.client import Mem0MemoryService
from src.infra.redis import get_redis_client
from src.services.cost_tracker import CostTrackerService
from src.settings import settings


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


def get_user_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserRepositoryProtocol:
    """
    Dependency that provides an initialized UserRepository.
    """
    return SqlAlchemyUserRepository(session)


async def get_cost_tracker() -> AsyncGenerator[CostTrackerService, None]:
    """
    Dependency that provides the CostTrackerService and cleans it up.
    """
    tracker = CostTrackerService(str(settings.REDIS_URL))
    try:
        yield tracker
    finally:
        await tracker.close()


__all__ = [
    "get_graph",
    "get_db_session",
    "get_memory_service",
    "get_sphere_repository",
    "get_user_repository",
    "get_redis_client",
    "get_cost_tracker",
]
