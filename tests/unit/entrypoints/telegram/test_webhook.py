from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.entrypoints.telegram.webhook import process_telegram_update, router


# Integration style test for the background task logic
@pytest.mark.asyncio
async def test_process_telegram_update_happy_path():
    # Mock Graph
    mock_graph = AsyncMock()
    mock_graph.ainvoke.return_value = {
        "messages": [{"content": "Hello from Agent"}],
        "step_count": 1,
    }

    # Mock TelegramClient
    with patch("src.entrypoints.telegram.webhook.TelegramClient") as MockClientClass:
        mock_client_instance = MockClientClass.return_value
        mock_client_instance.send_message = AsyncMock()
        mock_client_instance.close = AsyncMock()

        update_data = {
            "update_id": 123,
            "message": {
                "message_id": 1,
                "from": {"id": 999, "first_name": "Test"},
                "chat": {"id": 999, "type": "private"},
                "date": 123456,
                "text": "Hello Agent",
            },
        }

        await process_telegram_update(update_data, mock_graph)

        # Verify Graph called correctly
        mock_graph.ainvoke.assert_called_once()
        call_args = mock_graph.ainvoke.call_args
        assert call_args[0][0]["messages"][0]["content"] == "Hello Agent"
        assert call_args[0][0]["user_id"] == "999"
        assert call_args[1]["config"]["configurable"]["thread_id"] == "telegram_999"

        # Verify Message sent back
        mock_client_instance.send_message.assert_called_once_with(
            999, "Hello from Agent", reply_markup=None
        )
        mock_client_instance.close.assert_called_once()


@pytest.mark.asyncio
async def test_process_telegram_update_no_text():
    mock_graph = AsyncMock()

    with patch("src.entrypoints.telegram.webhook.TelegramClient") as MockClientClass:
        mock_client_instance = MockClientClass.return_value
        mock_client_instance.close = AsyncMock()

        # Update with photo, no text
        update_data = {
            "update_id": 124,
            "message": {
                "message_id": 2,
                "from": {"id": 999},
                "chat": {"id": 999},
                "photo": [],
            },
        }

        await process_telegram_update(update_data, mock_graph)

        # Graph should NOT be called
        mock_graph.ainvoke.assert_not_called()
        # No message sent
        mock_client_instance.send_message.assert_not_called()
        # Client closed
        mock_client_instance.close.assert_called_once()


# API Endpoint Test
# API Endpoint Test
def test_webhook_endpoint_accepted():
    from fastapi import FastAPI

    from src.app.dependencies import get_graph

    app = FastAPI()

    # We need to override get_graph
    app.dependency_overrides[get_graph] = lambda: AsyncMock()

    app.include_router(router)

    client = TestClient(app)

    payload = {"update_id": 1, "message": {"text": "ping"}}
    response = client.post("/telegram/webhook", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "accepted"}
