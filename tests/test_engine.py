from datetime import datetime, timedelta, timezone
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.db import crud
from app.engine.llm import LLMClient
from app.engine.processor import process_event
from app.engine.schema import LLMActionResponse, SpeakAction, SetTimerAction
from app.models import MessageRole, TaskStatus


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
async def test_llm_schema_validation():
    valid_json = {
        "actions": [
            {"type": "speak", "content": "Instant reply"},
            {"type": "set_timer", "delay_seconds": 30},
        ]
    }
    resp = LLMActionResponse.model_validate(valid_json)
    assert len(resp.actions) == 2
    assert isinstance(resp.actions[0], SpeakAction)
    assert isinstance(resp.actions[1], SetTimerAction)
    assert resp.actions[1].delay_seconds == 30

    # Test delay bounds: < 10 should fail
    with pytest.raises(ValidationError):
        SetTimerAction(delay_seconds=5)

    # Test delay bounds: > 60 should fail
    with pytest.raises(ValidationError):
        SetTimerAction(delay_seconds=120)


@pytest.mark.asyncio
async def test_event_processor_execution_and_set_timer(test_db: AsyncSession):
    session = await crud.create_session(test_db, system_prompt="Test Prompt")
    await crud.create_message(test_db, session.id, MessageRole.USER, "What is the status?")

    mock_llm = LLMClient()
    mock_llm.generate_actions = AsyncMock(
        return_value=LLMActionResponse(
            actions=[
                SpeakAction(content="Processing request"),
                SetTimerAction(delay_seconds=30),
            ]
        )
    )

    result = await process_event(test_db, session.id, llm_client=mock_llm)
    assert result["status"] == "success"
    assert result["spoken"] == 1
    assert result["timers_set"] == 1

    messages = await crud.get_messages_for_session(test_db, session.id)
    assert len(messages) == 2
    assert messages[1].content == "Processing request"


@pytest.mark.asyncio
async def test_pending_timer_autocancellation(test_db: AsyncSession):
    session = await crud.create_session(test_db, system_prompt="Test Prompt")
    future_time = datetime.now(timezone.utc) + timedelta(seconds=45)
    pending_task = await crud.create_scheduled_task(test_db, session.id, future_time)

    assert pending_task.status == TaskStatus.PENDING

    mock_llm = LLMClient()
    mock_llm.generate_actions = AsyncMock(
        return_value=LLMActionResponse(actions=[SpeakAction(content="New interaction")])
    )

    # Triggering new process_event should auto-cancel existing pending timer
    await process_event(test_db, session.id, llm_client=mock_llm)

    refreshed_task = await crud.get_scheduled_task(test_db, pending_task.id)
    assert refreshed_task is not None
    assert refreshed_task.status == TaskStatus.CANCELLED
