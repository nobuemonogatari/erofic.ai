from datetime import datetime, timedelta, timezone
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.models import MessageRole, TaskStatus
from app.db import crud


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_and_get_session(test_db: AsyncSession):
    session = await crud.create_session(test_db, system_prompt="You are a helpful assistant.")
    assert session.id is not None
    assert session.system_prompt == "You are a helpful assistant."

    fetched = await crud.get_session(test_db, session.id)
    assert fetched is not None
    assert fetched.id == session.id
    assert fetched.system_prompt == "You are a helpful assistant."


@pytest.mark.asyncio
async def test_create_and_get_messages(test_db: AsyncSession):
    session = await crud.create_session(test_db, system_prompt="Test Prompt")
    
    msg1 = await crud.create_message(test_db, session.id, MessageRole.USER, "Hello!")
    msg2 = await crud.create_message(test_db, session.id, MessageRole.ASSISTANT, "Hi there!")

    messages = await crud.get_messages_for_session(test_db, session.id)
    assert len(messages) == 2
    assert messages[0].role == MessageRole.USER
    assert messages[0].content == "Hello!"
    assert messages[1].role == MessageRole.ASSISTANT
    assert messages[1].content == "Hi there!"


@pytest.mark.asyncio
async def test_scheduled_task_lifecycle(test_db: AsyncSession):
    session = await crud.create_session(test_db, system_prompt="Scheduler Test")
    
    now = datetime.now(timezone.utc)
    execute_at_past = now - timedelta(seconds=10)
    execute_at_future = now + timedelta(seconds=120)

    task_due = await crud.create_scheduled_task(test_db, session.id, execute_at_past)
    task_future = await crud.create_scheduled_task(test_db, session.id, execute_at_future)

    pending_due = await crud.get_pending_tasks_due(test_db, now=now)
    assert len(pending_due) == 1
    assert pending_due[0].id == task_due.id

    updated_task = await crud.mark_task_status(test_db, task_due.id, TaskStatus.COMPLETED)
    assert updated_task is not None
    assert updated_task.status == TaskStatus.COMPLETED

    pending_due_after = await crud.get_pending_tasks_due(test_db, now=now)
    assert len(pending_due_after) == 0
