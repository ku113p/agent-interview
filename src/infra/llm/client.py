from typing import TypeVar

import structlog
from langfuse import observe
from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

from src.domain.ports.llm_provider import LLMProviderProtocol
from src.infra.llm.messages import convert_to_openai_messages
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
                # Mock CritiqueSchema for testing flows
                return schema.model_construct(
                    is_approved=True, feedback="Mock feedback", score=10
                )

            if schema.__name__ == "PlanSchema":
                # Mock PlanSchema for testing flows
                return schema.model_construct(
                    goal_analysis="Mock analysis", steps=[], missing_info=[]
                )

            return schema.model_construct()
        except Exception as e:
            log.error("llm_call_failed", error=str(e))
            from src.domain.exceptions import LLMError

            raise LLMError(f"Simulated LLM call failed: {str(e)}") from e


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

    @observe()
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
        clean_messages = convert_to_openai_messages(messages)
        # Type hack: OpenAI expects dicts, helper returns dicts
        system_msg = {"role": "system", "content": system_prompt}
        msgs = [system_msg] + clean_messages

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=msgs,  # type: ignore
            )
            content = response.choices[0].message.content or ""
            log.info("llm_call_success")
            return content
        except Exception as e:
            from src.domain.exceptions import LLMError, LLMMessageValidationError

            if isinstance(e, LLMMessageValidationError):
                raise e

            log.error("llm_call_failed", error=str(e))
            raise LLMError(f"LLM call failed: {str(e)}") from e

    @observe()
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

        clean_messages = convert_to_openai_messages(messages)
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
            from src.domain.exceptions import (
                LLMError,
                LLMMessageValidationError,
                LLMResponseError,
            )

            if isinstance(e, LLMMessageValidationError):
                raise e

            log.error("llm_call_failed", error=str(e))

            is_parse_error = (
                "parsing" in str(e).lower()
                or "structured" in str(e).lower()
                or isinstance(e, ValueError)
            )
            if is_parse_error:
                raise LLMResponseError(
                    f"Failed to parse structured output: {str(e)}"
                ) from e
            raise LLMError(f"LLM call failed: {str(e)}") from e


def get_llm_client() -> LLMProviderProtocol:
    if settings.USE_SIMULATED_LLM:
        return SimulatedOpenAIClient()
    return OpenAIClient()
