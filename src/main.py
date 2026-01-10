import asyncio
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

# Fix for psycopg on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.app.graph.workflow import create_graph
from src.entrypoints.api import health as health_router
from src.entrypoints.api import router as chat_router
from src.entrypoints.api import spheres as spheres_router
from src.entrypoints.api import users as users_router
from src.entrypoints.api.error_handlers import register_error_handlers
from src.entrypoints.telegram import webhook as webhook_router
from src.logging import configure_logging
from src.middleware.correlation import CorrelationIdMiddleware
from src.middleware.rate_limiter import RateLimitMiddleware
from src.settings import settings

# Configure logging immediately
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    database_url = str(settings.DATABASE_URL).replace("+asyncpg", "")

    async with AsyncPostgresSaver.from_conn_string(database_url) as checkpointer:
        await checkpointer.setup()

        app.state.graph = create_graph(checkpointer)

        yield


app = FastAPI(title="Modular Agentic Monolith", version="0.1.0", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    RateLimitMiddleware, redis_url=str(settings.REDIS_URL), limit=100, window=60
)
register_error_handlers(app)

app.include_router(chat_router.router)
app.include_router(users_router.router)
app.include_router(spheres_router.router)
app.include_router(health_router.router)
app.include_router(webhook_router.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "local",
    )
