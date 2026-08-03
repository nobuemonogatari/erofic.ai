from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db import crud
from app.db.base import Base
from app.engine.schema import LLMActionResponse, SpeakAction
from app.models import TaskStatus
from app.scheduler.worker import TaskSchedulerWorker


@pytest_asyncio.fixture
async def scheduler_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield session_factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_scheduler_worker_idempotency_and_execution(scheduler_env):
    session_factory = scheduler_env

    # Setup session and past due scheduled task
    async with session_factory() as db:
        session = await crud.create_session(db, system_prompt="Scheduler Prompt")
        past_time = datetime.now(timezone.utc) - timedelta(seconds=5)
        task = await crud.create_scheduled_task(db, session.id, execute_at=past_time)
        task_id = task.id

    worker = TaskSchedulerWorker(session_factory=session_factory)

    with patch(
        "app.engine.processor.LLMClient.generate_actions",
        new_callable=AsyncMock,
        return_value=LLMActionResponse(
            actions=[SpeakAction(content="Scheduled event trigger reply")]
        ),
    ):
        count = await worker.run_once()
        assert count == 1

    # Verify task was marked COMPLETED (idempotency) and message was added
    async with session_factory() as db:
        updated_task = await crud.get_scheduled_task(db, task_id)
        assert updated_task is not None
        assert updated_task.status == TaskStatus.COMPLETED

        messages = await crud.get_messages_for_session(db, session.id)
        assert len(messages) == 1
        assert messages[0].content == "Scheduled event trigger reply"
