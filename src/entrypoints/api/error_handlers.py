import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.domain.exceptions import BusinessRuleViolation, DomainError, ResourceNotFound

logger = structlog.get_logger()

def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(
        request: Request, exc: DomainError
    ) -> JSONResponse:
        status_code = 400
        if isinstance(exc, ResourceNotFound):
            status_code = 404
        elif isinstance(exc, BusinessRuleViolation):
            status_code = 400

        logger.error(
            "domain_error",
            path=request.url.path,
            error=exc.message,
            type=exc.__class__.__name__,
        )

        return JSONResponse(
            status_code=status_code,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("unhandled_exception", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred. Please try again later.",
            },
        )
