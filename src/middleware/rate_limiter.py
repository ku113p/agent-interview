import time
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit the number of requests per IP address using Redis.
    Uses a simple fixed-window algorithm.
    """

    def __init__(
        self,
        app: ASGIApp,
        redis_url: str,
        limit: int = 100,  # requests
        window: int = 60,  # seconds
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.redis_url = redis_url
        self.limit = limit
        self.window = window
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

        # Identify client by IP, respecting X-Forwarded-For
        client_ip = "unknown"
        if x_forwarded_for := request.headers.get("X-Forwarded-For"):
            # X-Forwarded-For: client, proxy1, proxy2
            client_ip = x_forwarded_for.split(",")[0].strip()
        elif request.client and request.client.host:
            client_ip = request.client.host

        # Use a fixed window based on time
        # Key format: rate_limit:{ip}:{minute_timestamp}
        # For MVP, fixed window per minute is acceptable.
        current_window = int(time.time() // self.window)
        key = f"rate_limit:{client_ip}:{current_window}"

        try:
            redis = await self._get_redis()

            # INCR returns the new value
            request_count = await redis.incr(key)

            # If first request, set expiration
            if request_count == 1:
                await redis.expire(key, self.window)

            if request_count > self.limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Too Many Requests",
                        "message": (
                            f"Rate limit exceeded. Try again in {self.window} seconds."
                        ),
                    },
                    headers={"Retry-After": str(self.window)},
                )

        except Exception:
            # Fail open if Redis is down
            # (don't block traffic due to rate limiter failure)
            # In a strict environment, we might fail closed.
            pass

        return await call_next(request)  # type: ignore
