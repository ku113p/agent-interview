from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.settings import settings

# Create Async Engine
# echo=True will log SQL queries for debugging in local env
engine = create_async_engine(
    str(settings.DATABASE_URL), echo=settings.ENVIRONMENT == "local", future=True
)

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
