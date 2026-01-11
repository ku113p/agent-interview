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

from src.entrypoints.telegram.formatting import markdown_to_telegram_html

logger = structlog.get_logger()


class TelegramClient:
    """
    Client for interacting with the Telegram Bot API.
    Converts Markdown input to Telegram HTML with fallback to raw text.
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
        Attempts to format as HTML first, falls back to raw text on error.
        """
        url = f"{self.base_url}/sendMessage"

        # Prepare fallback payload (raw text)
        payload_raw = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload_raw["reply_markup"] = reply_markup

        try:
            # Attempt 1: Convert Markdown to HTML and send
            html_text = markdown_to_telegram_html(text)
            payload_html = {"chat_id": chat_id, "text": html_text, "parse_mode": "HTML"}
            if reply_markup:
                payload_html["reply_markup"] = reply_markup

            response = await self.client.post(url, json=payload_html)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

        except (Exception, httpx.HTTPStatusError) as e:
            self._log_send_error(e, chat_id)

            # Check if we should fallback (formatting error or 400 Bad Request)
            is_400 = (
                isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 400
            )
            is_conversion_error = not isinstance(e, httpx.HTTPError)

            if not (is_400 or is_conversion_error):
                raise e

            # Attempt 2: Send raw text
            # We let this raise errors naturally so the @retry decorator handles it
            try:
                response = await self.client.post(url, json=payload_raw)
                response.raise_for_status()
                return cast(dict[str, Any], response.json())
            except httpx.HTTPStatusError as fallback_err:
                self._log_fallback_error(fallback_err)
                raise fallback_err

    def _log_send_error(self, e: Exception, chat_id: int) -> None:
        if isinstance(e, httpx.HTTPStatusError):
            logger.warning(
                "telegram_html_send_failed",
                error=str(e),
                status_code=e.response.status_code,
                response=e.response.text,
                chat_id=chat_id,
            )
        else:
            logger.warning(
                "telegram_markdown_conversion_failed", error=str(e), chat_id=chat_id
            )

    def _log_fallback_error(self, e: httpx.HTTPStatusError) -> None:
        logger.error(
            "telegram_send_raw_failed",
            error=str(e),
            status_code=e.response.status_code,
            response=e.response.text,
        )

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
