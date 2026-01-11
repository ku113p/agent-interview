import pytest
from sqlalchemy import text

from src.infra.db.session import engine
from src.settings import settings


@pytest.fixture(autouse=True)
async def cleanup_engine():
    """
    Explicitly dispose of the global engine after these tests.
    Since these tests interact with the global engine (to check configuration),
    we must ensure its pool is closed before the test loop terminates
    to avoid 'coroutine was never awaited' warnings.
    """
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_db_engine_configuration():
    """
    Verify that the AsyncEngine is configured with the correct pool settings
    defined in settings.py.
    """
    # Access the underlying pool from the sync engine
    pool = engine.sync_engine.pool

    assert pool.size() == settings.DB_POOL_SIZE
    # Note: max_overflow isn't directly exposed on some pool implementations
    # as a property dependent on the pool class (QueuePool usually).
    # We can check the protected attribute if we really need to, or rely on
    # initialization checks.
    # For QueuePool:
    assert pool._max_overflow == settings.DB_MAX_OVERFLOW
    assert pool._timeout == settings.DB_POOL_TIMEOUT
    assert pool._recycle == settings.DB_POOL_RECYCLE
    assert pool._pre_ping == settings.DB_POOL_PRE_PING


@pytest.mark.asyncio
async def test_db_monitoring_and_connectivity(caplog):
    """
    Verify that connection monitoring logs are emitted and connectivity works.
    """
    import logging

    # Ensure we capture DEBUG logs from the session module
    with caplog.at_level(logging.DEBUG, logger="src.infra.db.session"):
        async with engine.connect() as conn:
            # Doing a simple query to ensure connection is checked out
            # This also verifies connectivity
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    # Check for checkout log
    assert "DB connection checked out" in caplog.text
    # Check for checkin log
    assert "DB connection checked in" in caplog.text
