import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infra.db.models import Base
from src.settings import settings


@pytest.fixture(scope="function")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="function")
async def db_engine():
    # Use the project settings for DB URL
    # Replace +asyncpg if it's there twice or missing,
    # but usually settings.DATABASE_URL is correct
    url = str(settings.DATABASE_URL)
    engine = create_async_engine(url)

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """
    Yields an AsyncSession wrapped in a transaction that is rolled back after the test.
    This ensures tests don't pollute the database.
    """
    connection = await db_engine.connect()
    transaction = await connection.begin()

    session_factory = async_sessionmaker(
        bind=connection, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session

    await transaction.rollback()
    await connection.close()


@pytest.fixture
async def redis_client():
    client = Redis.from_url(str(settings.REDIS_URL), decode_responses=True)
    yield client
    await client.aclose()


@pytest.fixture(autouse=True)
def override_db_dependency(db_session):
    """
    Globally override the get_db_session dependency for all integration tests.
    This ensures all tests use the test-scoped session (rollback transaction)
    instead of the global engine's session, preventing data pollution and
    orphaned connection warnings.
    """
    from src.infra.db.session import get_db_session
    from src.main import app

    async def _override():
        yield db_session

    app.dependency_overrides[get_db_session] = _override
    yield
    app.dependency_overrides.pop(get_db_session, None)
