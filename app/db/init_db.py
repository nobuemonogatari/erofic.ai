from app.db.base import Base
from app.db.session import engine
from app.models.session import SessionModel
from app.models.message import MessageModel
from app.models.task import ScheduledTaskModel


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
