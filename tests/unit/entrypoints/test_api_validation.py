from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.app.dependencies import get_graph, get_memory_service, get_sphere_repository
from src.main import app


@pytest.fixture
def mock_graph() -> AsyncMock:
    """Create a mock graph for dependency injection."""
    graph = AsyncMock()
    # Mock ainvoke to prevent actual graph execution if validation passes
    graph.ainvoke = AsyncMock(return_value={"messages": [], "step_count": 0})
    return graph


@pytest.fixture
def client(mock_graph: AsyncMock) -> TestClient:
    """Create test client with mocked dependencies."""
    from unittest.mock import AsyncMock

    mock_memory = AsyncMock()
    app.dependency_overrides[get_memory_service] = lambda: mock_memory
    mock_sphere_repo = AsyncMock()
    app.dependency_overrides[get_sphere_repository] = lambda: mock_sphere_repo
    app.dependency_overrides[get_graph] = lambda: mock_graph

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_chat_message_validation_success(client: TestClient) -> None:
    """Test that valid messages are accepted."""
    response = client.post(
        "/v1/chat/message",
        json={
            "user_id": "test_user",
            "message": "Hello, world!",
            "thread_id": "valid_thread_123",
        },
    )
    assert response.status_code == 200


def test_chat_message_validation_too_long(client: TestClient) -> None:
    """Test that messages exceeding max length are rejected."""
    long_message = "a" * 4097
    response = client.post(
        "/v1/chat/message",
        json={
            "user_id": "test_user",
            "message": long_message,
            "thread_id": "test_thread",
        },
    )
    assert response.status_code == 422
    assert (
        "String should have at most" in response.text
        or "ensure this value has at most" in response.text
    )


def test_chat_message_validation_empty(client: TestClient) -> None:
    """Test that empty messages are rejected."""
    response = client.post(
        "/v1/chat/message",
        json={"user_id": "test_user", "message": "", "thread_id": "test_thread"},
    )
    assert response.status_code == 422
    assert (
        "String should have at least" in response.text
        or "ensure this value has at least" in response.text
    )


def test_thread_id_validation_invalid_chars(client: TestClient) -> None:
    """Test that thread_id with invalid characters is rejected."""
    response = client.post(
        "/v1/chat/message",
        json={
            "user_id": "test_user",
            "message": "Hello",
            "thread_id": "bad thread id!",  # spaces and special chars
        },
    )
    assert response.status_code == 422
    # Pydantic regex error message usually mentions "string does not match regex"
    assert "thread_id" in response.text


def test_user_id_validation_invalid_chars(client: TestClient) -> None:
    """Test that user_id with invalid characters is rejected."""
    response = client.post(
        "/v1/chat/message",
        json={"user_id": "bad user/id", "message": "Hello", "thread_id": "test_thread"},
    )
    assert response.status_code == 422
    assert "user_id" in response.text
