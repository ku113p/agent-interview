from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp


class BudgetMiddleware(BaseHTTPMiddleware):
    """
    Middleware to block requests when a user's total token budget is exceeded.
    """

    def __init__(
        self,
        app: ASGIApp,
        redis_url: str,
        budget_limit: int,
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.redis_url = redis_url
        self.budget_limit = budget_limit
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]
        self._redis: Redis | None = None

    async def _get_redis(self) -> Redis:
        """Lazy initialization of Redis client"""
        if self._redis is None:
            self._redis = Redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def dispatch(
        self, request: Request, call_next: Callable[..., Any]
    ) -> Response:
        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)  # type: ignore

        user_id = request.headers.get("X-User-ID")
        if not user_id:
            # If no user ID, we can't enforce user budget.
            # (Or we could enforce a global/IP budget, but that's not the req)
            return await call_next(request)  # type: ignore

        try:
            redis = await self._get_redis()
            base_key = f"usage:user:{user_id}"

            # Fetch usage stats
            # input_tokens and output_tokens are stored as strings
            values = await redis.mget(
                [f"{base_key}:input_tokens", f"{base_key}:output_tokens"]
            )

            input_tokens = int(values[0] or 0)
            output_tokens = int(values[1] or 0)
            total_tokens = input_tokens + output_tokens

            if total_tokens >= self.budget_limit:
                return JSONResponse(
                    status_code=429,  # or 402 Payment Required
                    content={
                        "error": "Budget Exceeded",
                        "message": (
                            f"Token budget of {self.budget_limit} exceeded. "
                            f"Current usage: {total_tokens} tokens."
                        ),
                    },
                )

        except Exception:
            # Fail open if Redis is down
            pass

        return await call_next(request)  # type: ignore
