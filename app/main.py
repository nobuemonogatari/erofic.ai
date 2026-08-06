from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import async_session_factory
from app.scheduler.manager import timer_manager
from app.api.routes import trigger_re_ping

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Mute verbose SQLite / SQLAlchemy query logs in DEBUG mode
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)
logging.getLogger("aiosqlite").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Core AI Chat Engine application...")
    logger.info(f"Loaded config - Database: {settings.DATABASE_URL}, Model: {settings.OPENAI_MODEL}, BaseURL: {settings.OPENAI_BASE_URL or 'default (OpenAI)'}")
    logger.info("Initializing database tables...")
    await init_db()
    logger.info("Running database seed check...")
    async with async_session_factory() as seed_session:
        from app.db.seed import seed_database
        await seed_database(seed_session)
    logger.info("Registering in-memory re-ping trigger callback...")
    timer_manager.register_trigger_fn(trigger_re_ping)

    yield
    # Shutdown
    logger.info("Application shutdown complete.")



app = FastAPI(
    title="Core AI Chat Engine",
    description="Headless event-driven chat engine simulating human conversational behavior.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root_frontend():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Core AI Chat Engine API active. Docs at /docs"}


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
