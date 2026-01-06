from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProviderProtocol(Protocol):
    """
    Abstract interface for generation to allow swapping providers.
    """

    async def generate(
        self, system_prompt: str, messages: list[dict[str, str]], schema: type[T]
    ) -> T:
        """
        Generate a structured response .
        """
        ...

    async def generate_text(
        self, system_prompt: str, messages: list[dict[str, str]]
    ) -> str:
        """Simple unstructured generation."""
        ...
