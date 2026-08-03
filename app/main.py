from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import async_session_factory
from app.scheduler.worker import TaskSchedulerWorker

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

scheduler_worker = TaskSchedulerWorker(session_factory=async_session_factory)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database tables...")
    await init_db()
    logger.info("Starting task scheduler background worker...")
    scheduler_worker.start()
    yield
    # Shutdown
    logger.info("Stopping task scheduler background worker...")
    await scheduler_worker.stop()


app = FastAPI(
    title="Core AI Chat Engine",
    description="Headless event-driven chat engine simulating human conversational behavior.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
