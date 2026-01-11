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
        limit: int = 100,  # User limit (requests/min)
        ip_limit: int = 1000,  # IP limit (requests/min)
        window: int = 60,  # seconds
        exclude_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.redis_url = redis_url
        self.limit = limit
        self.ip_limit = ip_limit
        self.window = window
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]
        self._redis: Redis | None = None

    async def _get_redis(self) -> Redis:
        """Lazy initialization of Redis client"""
        if self._redis is None:
            self._redis = Redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    def _get_client_ip(self, request: Request) -> str:
        if x_forwarded_for := request.headers.get("X-Forwarded-For"):
            return x_forwarded_for.split(",")[0].strip()
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    async def dispatch(
        self, request: Request, call_next: Callable[..., Any]
    ) -> Response:
        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)  # type: ignore

        client_ip = self._get_client_ip(request)
        user_id = request.headers.get("X-User-ID")
        current_window = int(time.time() // self.window)

        try:
            redis = await self._get_redis()
            pipe = redis.pipeline()

            # IP Key
            ip_key = f"rate_limit:{client_ip}:{current_window}"
            pipe.incr(ip_key)
            pipe.expire(ip_key, self.window)

            # User Key (if present)
            if user_id:
                user_key = f"rate_limit:user:{user_id}:{current_window}"
                pipe.incr(user_key)
                pipe.expire(user_key, self.window)

            results = await pipe.execute()

            # Check limits
            # results = [ip_count, ip_expire_success, user_count, user_expire_success]
            if results[0] > self.ip_limit:
                return self._rate_limit_response(self.window)

            if user_id and results[2] > self.limit:
                return self._rate_limit_response(self.window)

        except Exception:
            # Fail open if Redis is down
            pass

        return await call_next(request)  # type: ignore

    def _rate_limit_response(self, retry_after: int) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too Many Requests",
                "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
            },
            headers={"Retry-After": str(retry_after)},
        )
