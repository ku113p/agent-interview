from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from redis.asyncio import Redis as AsyncRedis

from src.app.dependencies import get_db_session
from src.infra.redis import get_redis_client
from src.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_check_healthy(client: TestClient):
    """Test health check when all services are healthy."""
    # Mock DB
    mock_db = AsyncMock()
    mock_db.execute.return_value = None

    # Mock Redis
    mock_redis = AsyncMock(spec=AsyncRedis)
    # Configure ping to be awaitable
    mock_redis.ping = AsyncMock(return_value=True)

    # Override dependencies
    app.dependency_overrides[get_db_session] = lambda: mock_db
    app.dependency_overrides[get_redis_client] = lambda: mock_redis

    try:
        response = client.get("/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "ok"
        assert data["redis"] == "ok"
    finally:
        app.dependency_overrides.clear()


def test_health_check_db_failure(client: TestClient):
    """Test health check when database is down."""
    mock_db = AsyncMock()
    mock_db.execute.side_effect = Exception("DB Connection Failed")

    mock_redis = AsyncMock(spec=AsyncRedis)
    mock_redis.ping = AsyncMock(return_value=True)

    app.dependency_overrides[get_db_session] = lambda: mock_db
    app.dependency_overrides[get_redis_client] = lambda: mock_redis

    try:
        response = client.get("/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert "DB Connection Failed" in data["database"]
        assert data["redis"] == "ok"
    finally:
        app.dependency_overrides.clear()


def test_health_check_redis_failure(client: TestClient):
    """Test health check when Redis is down."""
    mock_db = AsyncMock()
    mock_db.execute.return_value = None

    mock_redis = AsyncMock(spec=AsyncRedis)
    mock_redis.ping.side_effect = Exception("Redis Connection Refused")

    app.dependency_overrides[get_db_session] = lambda: mock_db
    app.dependency_overrides[get_redis_client] = lambda: mock_redis

    try:
        response = client.get("/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "ok"
        assert "Redis Connection Refused" in data["redis"]
    finally:
        app.dependency_overrides.clear()


def test_health_check_total_failure(client: TestClient):
    """Test health check when both services are down."""
    mock_db = AsyncMock()
    mock_db.execute.side_effect = Exception("DB Error")

    mock_redis = AsyncMock(spec=AsyncRedis)
    mock_redis.ping.side_effect = Exception("Redis Error")

    app.dependency_overrides[get_db_session] = lambda: mock_db
    app.dependency_overrides[get_redis_client] = lambda: mock_redis

    try:
        response = client.get("/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert "DB Error" in data["database"]
        assert "Redis Error" in data["redis"]
    finally:
        app.dependency_overrides.clear()
