import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.logging import request_id_var

logger = structlog.get_logger()


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that assigns a correlation ID (request ID) to each request.
    It binds this ID to the logging context and includes it in the response headers.
    It also logs the request completion with performance metrics.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 1. Extract or Generate Request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # 2. Set Context for Logging
        token = request_id_var.set(request_id)

        # 3. Process Request
        start_time = time.perf_counter()

        # Bind request_id to this specific logger instance for redundancy
        # (though the processor handles it globally via ContextVar)
        log = logger.bind()

        try:
            response = await call_next(request)

            # 4. Calculate Duration
            process_time = time.perf_counter() - start_time
            duration_ms = round(process_time * 1000, 2)

            # 5. Log Success
            log.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_agent=request.headers.get("user-agent"),
            )

            # 6. Add Header to Response
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            # Calculate duration even for errors
            process_time = time.perf_counter() - start_time
            duration_ms = round(process_time * 1000, 2)

            log.error(
                "http_request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                error=str(e),
            )
            raise e

        finally:
            # 7. Cleanup Context
            request_id_var.reset(token)
