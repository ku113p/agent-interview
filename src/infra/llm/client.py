from typing import TypeVar

import structlog
from pydantic import BaseModel
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)

from src.domain.ports.llm_provider import LLMProviderProtocol

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
        reraise=True
    )
    async def generate(
        self, 
        system_prompt: str, 
        messages: list[dict[str, str]], 
        schema: type[T]
    ) -> T:
        """
        Generates structured output.
        """
        log = logger.bind(method="generate_structured", schema=schema.__name__)
        log.info("llm_call_start")

        try:
            if schema.__name__ == "CritiqueSchema":
                return schema.model_construct(
                    is_approved=True, 
                    feedback="Mock feedback", 
                    score=10
                )
            
            if schema.__name__ == "PlanSchema":
                return schema.model_construct(
                    goal_analysis="Mock analysis",
                    steps=[],
                    missing_info=[]
                )

            return schema.model_construct()
        except Exception as e:
            log.error("llm_call_failed", error=str(e))
            raise e
