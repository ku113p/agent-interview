from src.app.prompts.renderer import render_prompt
from src.domain.ports.llm_provider import LLMProviderProtocol
from src.domain.value_objects import Message


class ContextManager:
    def __init__(self, llm_client: LLMProviderProtocol):
        self.llm_client = llm_client

    async def summarize_conversation(
        self, current_summary: str, messages: list[Message], user_id: str | None = None
    ) -> str:
        """
        Generates a new summary by combining the existing summary with new messages.
        """
        # Format messages for the prompt
        formatted_messages = []
        for msg in messages:
            content = msg.content
            role = msg.role
            formatted_messages.append(f"{role.upper()}: {content}")

        messages_text = "\n".join(formatted_messages)

        system_prompt = render_prompt(
            "summarizer",
            user_id=user_id,
            current_summary=current_summary or "No previous summary.",
            new_messages=messages_text,
        )

        # We use a simple generate_text call here as we want a string summary
        new_summary = await self.llm_client.generate_text(
            system_prompt=system_prompt,
            messages=[],  # The content is fully in the system prompt for this task
        )

        return new_summary
