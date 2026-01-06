from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.domain.entities.memory import MemoryFragment, MemoryKind
from src.infra.vector.memory import RedisMemoryService


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Create a mock Redis client."""
    return AsyncMock()


@pytest.fixture
def memory_service(mock_redis: AsyncMock) -> RedisMemoryService:
    """Create RedisMemoryService with mocked Redis."""
    return RedisMemoryService(redis=mock_redis)


@pytest.mark.asyncio
async def test_add_memory_fragment(
    memory_service: RedisMemoryService, mock_redis: AsyncMock
) -> None:
    """Test that add() stores memory fragment in Redis."""
    user_id = uuid4()
    fragment = MemoryFragment(
        content="Python programming knowledge",
        kind=MemoryKind.SEMANTIC,
        user_id=user_id,
        importance=8,
    )

    await memory_service.add(fragment)

    # Verify Redis lpush was called with correct key and data
    expected_key = f"user:{user_id}:memories"
    mock_redis.lpush.assert_called_once()
    call_args = mock_redis.lpush.call_args
    assert call_args[0][0] == expected_key
    assert "Python programming knowledge" in call_args[0][1]


@pytest.mark.asyncio
async def test_get_recent_memories(
    memory_service: RedisMemoryService, mock_redis: AsyncMock
) -> None:
    """Test that get_recent() retrieves and parses memory fragments."""
    user_id = uuid4()
    fragment_data = MemoryFragment(
        content="Test memory",
        kind=MemoryKind.FACTUAL,
        user_id=user_id,
        importance=5,
    )

    # Mock Redis lrange to return serialized fragment
    mock_redis.lrange.return_value = [fragment_data.model_dump_json().encode()]

    results = await memory_service.get_recent(user_id, limit=10)

    assert len(results) == 1
    assert results[0].content == "Test memory"
    assert results[0].kind == MemoryKind.FACTUAL
    assert results[0].user_id == user_id


@pytest.mark.asyncio
async def test_get_recent_handles_empty_results(
    memory_service: RedisMemoryService, mock_redis: AsyncMock
) -> None:
    """Test that get_recent() handles empty Redis response."""
    user_id = uuid4()
    mock_redis.lrange.return_value = []

    results = await memory_service.get_recent(user_id, limit=10)

    assert results == []


@pytest.mark.asyncio
async def test_get_recent_skips_invalid_data(
    memory_service: RedisMemoryService, mock_redis: AsyncMock
) -> None:
    """Test that get_recent() gracefully skips malformed data."""
    user_id = uuid4()
    valid_fragment = MemoryFragment(
        content="Valid memory", kind=MemoryKind.SEMANTIC, user_id=user_id, importance=3
    )

    # Mix valid and invalid data
    mock_redis.lrange.return_value = [
        b"invalid json{",
        valid_fragment.model_dump_json().encode(),
        b'{"incomplete": "data"}',
    ]

    results = await memory_service.get_recent(user_id, limit=10)

    # Should only return the valid fragment
    assert len(results) == 1
    assert results[0].content == "Valid memory"


@pytest.mark.asyncio
async def test_search_delegates_to_get_recent(
    memory_service: RedisMemoryService, mock_redis: AsyncMock
) -> None:
    """Test that search() currently delegates to get_recent() (mock implementation)."""
    user_id = uuid4()
    mock_redis.lrange.return_value = []

    results = await memory_service.search(
        query="python", user_id=user_id, kind=MemoryKind.SEMANTIC, limit=5
    )

    # Verify it calls lrange (via get_recent)
    mock_redis.lrange.assert_called_once()
    assert isinstance(results, list)
