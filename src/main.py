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
from src.entrypoints.api import router as api_router
from src.entrypoints.api.error_handlers import register_error_handlers
from src.entrypoints.telegram import webhook
from src.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    database_url = str(settings.DATABASE_URL).replace("+asyncpg", "")

    async with AsyncPostgresSaver.from_conn_string(database_url) as checkpointer:
        await checkpointer.setup()

        app.state.graph = create_graph(checkpointer)

        yield


app = FastAPI(title="Modular Agentic Monolith", version="0.1.0", lifespan=lifespan)
register_error_handlers(app)

app.include_router(api_router.router)
app.include_router(webhook.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "local",
    )
