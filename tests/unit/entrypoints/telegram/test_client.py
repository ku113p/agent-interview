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
