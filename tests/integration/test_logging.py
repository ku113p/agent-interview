import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_request_id_in_response_headers() -> None:
    """
    Verifies that the API adds the X-Request-ID header to responses.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health/")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


@pytest.mark.asyncio
async def test_correlation_id_persistence() -> None:
    """
    Verifies that if a client sends an X-Request-ID, the server respects it
    and returns it in the response (trace continuity).
    """
    custom_trace_id = "trace-12345-test"
    headers = {"X-Request-ID": custom_trace_id}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health/", headers=headers)

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_trace_id
