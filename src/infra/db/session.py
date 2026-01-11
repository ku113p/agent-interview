import logging
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.settings import settings

logger = logging.getLogger(__name__)

# Create Async Engine
# echo=True will log SQL queries for debugging in local env
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.ENVIRONMENT == "local",
    future=True,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
)


# Connection Pool Monitoring
@event.listens_for(engine.sync_engine, "connect")
def log_connect(dbapi_connection: Any, connection_record: Any) -> None:
    logger.debug("New DB connection created", extra={"pool_id": id(connection_record)})


@event.listens_for(engine.sync_engine, "checkout")
def log_checkout(
    dbapi_connection: Any, connection_record: Any, connection_proxy: Any
) -> None:
    logger.debug("DB connection checked out", extra={"pool_id": id(connection_record)})


@event.listens_for(engine.sync_engine, "checkin")
def log_checkin(dbapi_connection: Any, connection_record: Any) -> None:
    logger.debug("DB connection checked in", extra={"pool_id": id(connection_record)})


# Configured Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False, class_=AsyncSession
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI.
    Yields an AsyncSession and ensures it's closed after the request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
