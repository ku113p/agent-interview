from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.app.dependencies import get_graph, get_memory_service, get_sphere_repository
from src.main import app


@pytest.fixture
def mock_graph() -> AsyncMock:
    """Create a mock graph for dependency injection."""
    graph = AsyncMock()

    # Mock ainvoke response
    graph.ainvoke = AsyncMock(
        return_value={
            "messages": [{"role": "assistant", "content": "Test response"}],
            "step_count": 3,
            "last_agent": "interviewer",
        }
    )

    # Mock aget_state response
    state_snapshot = MagicMock()
    state_snapshot.values = {
        "user_id": "test_user",
        "plan": {"goal_analysis": "Test plan", "steps": []},
        "critique": {"is_approved": True, "score": 10, "feedback": "Good job"},
        "last_agent": "interviewer",
        "step_count": 3,
        "messages": [],
    }
    graph.aget_state = AsyncMock(return_value=state_snapshot)

    return graph


@pytest.fixture
def client(mock_graph: AsyncMock) -> Generator[TestClient, None, None]:
    """Create test client with mocked dependencies."""
    from unittest.mock import AsyncMock

    # Mock memory service
    mock_memory = AsyncMock()
    app.dependency_overrides[get_memory_service] = lambda: mock_memory

    # Mock sphere repository
    mock_sphere_repo = AsyncMock()
    app.dependency_overrides[get_sphere_repository] = lambda: mock_sphere_repo

    app.dependency_overrides[get_graph] = lambda: mock_graph
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_chat_message_endpoint_success(client: TestClient) -> None:
    """Test that /message endpoint returns a valid response."""
    response = client.post(
        "/v1/chat/message",
        json={"user_id": "test_user", "message": "Hello", "thread_id": "test_thread"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "step_count" in data
    assert data["step_count"] == 3


def test_get_state_endpoint_success(client: TestClient) -> None:
    """Test that /debug/state endpoint returns thread state."""
    response = client.get("/v1/chat/debug/state/test_thread")

    assert response.status_code == 200
    data = response.json()
    assert "plan" in data
    # Internal fields should be hidden
    assert "last_agent" not in data
    assert "error_count" not in data
    # Public fields should be present
    assert data["user_id"] == "test_user"
    assert data["step_count"] == 3


def test_get_state_endpoint_not_found(
    client: TestClient, mock_graph: AsyncMock
) -> None:
    """Test that /debug/state returns 404 if state not found."""
    # Mock aget_state to return empty values
    state_snapshot = MagicMock()
    state_snapshot.values = {}
    mock_graph.aget_state = AsyncMock(return_value=state_snapshot)

    response = client.get("/v1/chat/debug/state/missing_thread")

    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "ResourceNotFound"
    assert "not found" in data["message"]


def test_chat_message_endpoint_domain_error(
    client: TestClient, mock_graph: AsyncMock
) -> None:
    """Test that /message handles domain errors correctly."""
    from src.domain.exceptions import BusinessRuleViolation

    mock_graph.ainvoke.side_effect = BusinessRuleViolation("Too many retries")

    response = client.post(
        "/v1/chat/message",
        json={"user_id": "test_user", "message": "Hello"},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "BusinessRuleViolation"
    assert data["message"] == "Too many retries"


def test_chat_message_endpoint_profanity(client: TestClient) -> None:
    """Test that /message rejects profane content."""

    # We patch contains_profanity to ensure it triggers
    with patch("src.entrypoints.api.router.contains_profanity", return_value=True):
        response = client.post(
            "/v1/chat/message",
            json={"user_id": "test_user", "message": "badword"},
        )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Message contains inappropriate content."
