import structlog
from fastapi import APIRouter, HTTPException, Request

logger = structlog.get_logger()
router = APIRouter(prefix="/telegram")


@router.post("/webhook")
async def telegram_webhook(request: Request) -> dict[str, str]:
    """
    Receives updates from Telegram.
    """
    try:
        data = await request.json()
        logger.info("telegram_update_received", data=data)

        return {"status": "ok"}
    except Exception as e:
        logger.error("telegram_webhook_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error") from e
