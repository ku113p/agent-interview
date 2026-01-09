from typing import Any, cast

import httpx
import structlog
from pydantic import SecretStr
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger()


class TelegramClient:
    """
    Client for interacting with the Telegram Bot API.
    """

    def __init__(self, token: SecretStr):
        self.base_url = f"https://api.telegram.org/bot{token.get_secret_value()}"
        self.client = httpx.AsyncClient(timeout=10.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(
            (httpx.NetworkError, httpx.TimeoutException, httpx.HTTPStatusError)
        ),
        reraise=True,
    )
    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Sends a text message to a chat, optionally with inline keyboard.
        """
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
        except httpx.HTTPStatusError as e:
            logger.error(
                "telegram_send_message_failed",
                error=str(e),
                status_code=e.response.status_code,
                response=e.response.text,
            )
            raise
        except Exception as e:
            logger.error("telegram_send_message_error", error=str(e))
            raise

    async def answer_callback_query(self, query_id: str) -> dict[str, Any]:
        """
        Answers a callback query to remove the loading state from buttons.
        """
        url = f"{self.base_url}/answerCallbackQuery"
        payload = {"callback_query_id": query_id}

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
        except Exception as e:
            logger.error("answer_callback_query_error", error=str(e))
            raise

    async def close(self) -> None:
        await self.client.aclose()
