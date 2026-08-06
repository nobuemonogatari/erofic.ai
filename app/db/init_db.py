from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401 registers all models with Base.metadata



from sqlalchemy import text


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Migration check for pre-existing SQLite databases missing scene_config_id on sessions table
        try:
            await conn.execute(text("ALTER TABLE sessions ADD COLUMN scene_config_id VARCHAR(36) REFERENCES scene_configs(id) ON DELETE SET NULL"))
        except Exception:
            # Column already exists
            pass

