from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx
from pydantic import SecretStr

from src.entrypoints.telegram.client import TelegramClient


@pytest.fixture
def client():
    return TelegramClient(SecretStr("123:ABC-TEST"))


@pytest.mark.asyncio
async def test_send_message_success(client):
    async with respx.mock(
        base_url="https://api.telegram.org/bot123:ABC-TEST"
    ) as respx_mock:
        route = respx_mock.post("/sendMessage").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )

        response = await client.send_message(12345, "Hello")

        assert response == {"ok": True}
        assert route.called
        import json

        last_request = route.calls.last.request
        assert json.loads(last_request.content) == {
            "chat_id": 12345,
            "text": "Hello",
            "parse_mode": "HTML",
        }


@pytest.mark.asyncio
async def test_send_message_retry_on_network_error(client):
    # Simulate 2 failures then success
    async with respx.mock(
        base_url="https://api.telegram.org/bot123:ABC-TEST"
    ) as respx_mock:
        route = respx_mock.post("/sendMessage").mock(
            side_effect=[
                httpx.NetworkError("Connection lost"),
                httpx.NetworkError("Connection lost"),
                httpx.Response(200, json={"ok": True}),
            ]
        )

        # Patch asyncio.sleep to skip wait times
        with patch("asyncio.sleep", new_callable=AsyncMock):
            response = await client.send_message(12345, "Hello")

        assert response == {"ok": True}
        assert route.call_count == 3


@pytest.mark.asyncio
async def test_send_message_failure(client):
    async with respx.mock(
        base_url="https://api.telegram.org/bot123:ABC-TEST"
    ) as respx_mock:
        respx_mock.post("/sendMessage").mock(
            return_value=httpx.Response(
                401, json={"ok": False, "description": "Unauthorized"}
            )
        )

        with pytest.raises(httpx.HTTPStatusError):
            await client.send_message(12345, "Hello")


@pytest.mark.asyncio
async def test_send_message_fallback_on_400(client):
    """
    Test that if the API returns 400 (Bad Request), likely due to formatting,
    the client retries with raw text and parse_mode=None.
    """
    async with respx.mock(
        base_url="https://api.telegram.org/bot123:ABC-TEST"
    ) as respx_mock:
        # Mock 1st call fails with 400
        # Mock 2nd call succeeds (fallback)
        route = respx_mock.post("/sendMessage").mock(
            side_effect=[
                httpx.Response(
                    400,
                    json={
                        "ok": False,
                        "description": "Bad Request: can't parse entities",
                    },
                ),
                httpx.Response(200, json={"ok": True}),
            ]
        )

        response = await client.send_message(12345, "**Bad Markdown**")

        assert response == {"ok": True}
        assert route.call_count == 2

        # Check first request (HTML)
        import json

        req1 = route.calls[0].request
        payload1 = json.loads(req1.content)
        assert payload1["parse_mode"] == "HTML"
        assert (
            "<b>Bad Markdown</b>" in payload1["text"]
        )  # Converter worked, but API rejected it

        # Check second request (Raw Fallback)
        req2 = route.calls[1].request
        payload2 = json.loads(req2.content)
        assert "parse_mode" not in payload2 or payload2["parse_mode"] is None
        assert payload2["text"] == "**Bad Markdown**"  # Original text sent
