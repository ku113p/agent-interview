from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.app.dependencies import get_cost_tracker, get_user_repository
from src.domain.entities.user import UserProfile
from src.main import app


@pytest.fixture
def mock_user_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_cost_tracker():
    tracker = AsyncMock()
    return tracker


@pytest.fixture
def client(mock_user_repo, mock_cost_tracker):
    app.dependency_overrides[get_user_repository] = lambda: mock_user_repo
    app.dependency_overrides[get_cost_tracker] = lambda: mock_cost_tracker
    with TestClient(app) as c:
        yield c
    app.dependency_overrides = {}


def test_admin_dashboard_html(client):
    response = client.get("/v1/admin/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<title>Admin Dashboard</title>" in response.text


@pytest.mark.asyncio
async def test_admin_usage_api(client, mock_user_repo, mock_cost_tracker):
    # Setup data
    uid1 = uuid4()
    uid2 = uuid4()

    user1 = UserProfile(
        id=uid1, email="u1@example.com", is_active=True, created_at=datetime.now(UTC)
    )
    user2 = UserProfile(
        id=uid2, email="u2@example.com", is_active=True, created_at=datetime.now(UTC)
    )

    # Needs to return a coroutine result or just list if using AsyncMock with
    # return_value properly set for awaitable?
    # AsyncMock return_value is returned when awaited.
    mock_user_repo.list_all.return_value = [user1, user2]

    mock_cost_tracker.get_bulk_usage.return_value = {
        str(uid1): {"input_tokens": 100, "output_tokens": 50},
        str(uid2): {"input_tokens": 200, "output_tokens": 150},
    }

    response = client.get("/v1/admin/usage")

    assert response.status_code == 200
    data = response.json()

    assert data["total_users"] == 2
    assert data["total_usage"]["input_tokens"] == 300
    assert data["total_usage"]["output_tokens"] == 200
    assert len(data["users"]) == 2

    # Verify call args
    mock_user_repo.list_all.assert_called_once()
    # Check that args were passed correctly. The arg is a list of strings.
    # We can inspect the call args.
    call_args = mock_cost_tracker.get_bulk_usage.call_args[0][0]
    assert set(call_args) == {str(uid1), str(uid2)}
