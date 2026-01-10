from redis.asyncio import Redis

from src.settings import settings


class CostTrackerService:
    """
    Service to track LLM token usage and costs per user.
    """

    def __init__(self, redis_url: str | None = None):
        url = redis_url or str(settings.REDIS_URL)
        self.redis = Redis.from_url(url, decode_responses=True)

    async def track_usage(
        self, user_id: str, model: str, input_tokens: int, output_tokens: int
    ) -> None:
        """
        Increment token usage counters for a user.
        """
        try:
            # Pipeline updates for atomicity
            pipe = self.redis.pipeline()

            # Keys
            base_key = f"usage:user:{user_id}"
            model_key = f"{base_key}:{model}"

            # Global user usage
            pipe.incrby(f"{base_key}:input_tokens", input_tokens)
            pipe.incrby(f"{base_key}:output_tokens", output_tokens)

            # Per-model usage
            pipe.incrby(f"{model_key}:input_tokens", input_tokens)
            pipe.incrby(f"{model_key}:output_tokens", output_tokens)

            await pipe.execute()
        except Exception:
            # Don't fail the request if stats tracking fails
            pass

    async def get_usage(self, user_id: str) -> dict[str, int]:
        """
        Get total token usage for a user.
        """
        base_key = f"usage:user:{user_id}"

        input_tokens = await self.redis.get(f"{base_key}:input_tokens") or 0
        output_tokens = await self.redis.get(f"{base_key}:output_tokens") or 0

        return {
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
        }

    async def close(self) -> None:
        await self.redis.aclose()
