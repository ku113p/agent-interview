from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.infra.db.session import get_db_session
from src.main import app


@pytest.fixture
def override_get_db_session(db_session):
    async def _override():
        yield db_session

    app.dependency_overrides[get_db_session] = _override
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check(override_get_db_session):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_user_creation_flow(override_get_db_session):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Create User
        email = f"api_test_{uuid4()}@example.com"
        user_id = str(uuid4())
        create_payload = {
            "id": user_id,
            "email": email,
            "full_name": "API User",
            "profession": "Tester",
            "experience_years": 3,
        }

        response = await ac.post("/v1/users/", json=create_payload)
        assert response.status_code == 200
        user_data = response.json()
        assert user_data["email"] == email
        assert user_data["id"] == user_id

        # Get User
        response = await ac.get(f"/v1/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["id"] == user_id
