from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dependencies import get_db_session
from src.infra.redis import get_redis_client

router = APIRouter(prefix="/health", tags=["System"])


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check(
    db: AsyncSession = Depends(get_db_session),  # noqa: B008
    redis: AsyncRedis = Depends(get_redis_client),  # noqa: B008
) -> dict[str, str]:
    """
    Checks the health of the application and its dependencies.
    """
    health_status = {"status": "ok", "database": "ok", "redis": "ok"}

    # Check Database
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis
    try:
        await redis.ping()  # type: ignore
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    return health_status
