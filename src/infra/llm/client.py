from typing import Any, TypeVar

import structlog
from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

from src.domain.ports.llm_provider import LLMProviderProtocol
from src.settings import settings

logger = structlog.get_logger()
T = TypeVar("T", bound=BaseModel)


class SimulatedOpenAIClient(LLMProviderProtocol):
    """
    A simulated client that implements resilience patterns.
    """

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate_text(
        self, system_prompt: str, messages: list[dict[str, str]]
    ) -> str:
        log = logger.bind(method="generate_text")
        log.info("llm_call_start", system_prompt_preview=system_prompt[:50])
        log.info("llm_call_success")
        return "Simulated generic response from LLM."

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate(
        self, system_prompt: str, messages: list[dict[str, str]], schema: type[T]
    ) -> T:
        """
        Generates structured output.
        """
        log = logger.bind(method="generate_structured", schema=schema.__name__)
        log.info("llm_call_start")

        try:
            if schema.__name__ == "CritiqueSchema":
                return schema.model_construct(
                    is_approved=True, feedback="Mock feedback", score=10
                )

            if schema.__name__ == "PlanSchema":
                return schema.model_construct(
                    goal_analysis="Mock analysis", steps=[], missing_info=[]
                )

            return schema.model_construct()
        except Exception as e:
            log.error("llm_call_failed", error=str(e))
            raise e


class OpenAIClient(LLMProviderProtocol):
    """
    Real OpenAI (or compatible) client.
    """

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
            base_url=settings.OPENAI_BASE_URL,
        )
        self.model = settings.MODEL_NAME

    def _convert_messages(self, messages: list[Any]) -> list[dict[str, str]]:
        """Converts diverse message formats to OpenAI dict format."""
        formatted = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted.append(msg)
            elif hasattr(msg, "content") and hasattr(msg, "type"):
                # LangChain BaseMessage support
                role = "user"
                if msg.type == "human":
                    role = "user"
                elif msg.type == "ai":
                    role = "assistant"
                elif msg.type == "system":
                    role = "system"
                elif msg.type == "chat":
                    role = "user"  # Fallback
                elif msg.type == "tool":
                    role = "tool"

                formatted.append({"role": role, "content": str(msg.content)})
            else:
                # Fallback purely to ensure we send something string-like
                formatted.append({"role": "user", "content": str(msg)})
        return formatted

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate_text(
        self, system_prompt: str, messages: list[dict[str, str]]
    ) -> str:
        log = logger.bind(method="generate_text", model=self.model)
        log.info("llm_call_start")

        # Prepare messages
        clean_messages = self._convert_messages(messages)
        msgs = [{"role": "system", "content": system_prompt}] + clean_messages

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=msgs,  # type: ignore
            )
            content = response.choices[0].message.content or ""
            log.info("llm_call_success")
            return content
        except Exception as e:
            log.error("llm_call_failed", error=str(e))
            raise e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def generate(
        self, system_prompt: str, messages: list[dict[str, str]], schema: type[T]
    ) -> T:
        log = logger.bind(
            method="generate_structured", schema=schema.__name__, model=self.model
        )
        log.info("llm_call_start")

        clean_messages = self._convert_messages(messages)
        msgs = [{"role": "system", "content": system_prompt}] + clean_messages

        try:
            response = await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=msgs,  # type: ignore
                response_format=schema,
            )
            parsed = response.choices[0].message.parsed
            if not parsed:
                raise ValueError("Failed to parse structured output")

            log.info("llm_call_success")
            return parsed
        except Exception as e:
            log.error("llm_call_failed", error=str(e))
            raise e


def get_llm_client() -> LLMProviderProtocol:
    if settings.USE_SIMULATED_LLM:
        return SimulatedOpenAIClient()
    return OpenAIClient()
