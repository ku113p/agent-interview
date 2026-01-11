import logging
import random
import sys
from collections.abc import MutableMapping
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.types import Processor

from src.settings import settings

# ContextVar to store the request ID
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def add_request_id(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """
    Structlog processor that adds the request_id from contextvars to the log event.
    """
    request_id = request_id_var.get()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def sampling_processor(
    logger: Any, method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    """
    Structlog processor that drops INFO/DEBUG logs based on the configured sample rate.
    WARNING, ERROR, and CRITICAL logs are always preserved.
    """
    # If settings.LOG_SAMPLE_RATE is 1.0, we keep everything (optimization)
    if settings.LOG_SAMPLE_RATE >= 1.0:
        return event_dict

    # Extract log level (added by previous processor)
    # Default to "info" if not present (safety fallback)
    level = event_dict.get("level", "info").lower()

    if level in ("info", "debug"):
        if random.random() > settings.LOG_SAMPLE_RATE:
            raise structlog.DropEvent

    return event_dict


def configure_logging() -> None:
    """
    Configures structlog and standard logging.
    """
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_request_id,
        structlog.processors.add_log_level,
        sampling_processor,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # If running in a local environment, add colors and use ConsoleRenderer
    # Otherwise (prod), use JSONRenderer
    # We do NOT render here when using structlog.stdlib.LoggerFactory
    # Instead we prepare it for the ProcessorFormatter
    structlog.configure(
        processors=shared_processors
        + [structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    handler = logging.StreamHandler(sys.stdout)

    # Use structlog for formatting standard library logs
    # This allows libraries using standard logging to be formatted by structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer()
            if settings.ENVIRONMENT == "local"
            else structlog.processors.JSONRenderer(),
        ],
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(settings.LOG_LEVEL.upper())

    # Prevent duplicated logs if using uvicorn/fastapi
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.error").handlers = []
    logging.getLogger("uvicorn").handlers = []
