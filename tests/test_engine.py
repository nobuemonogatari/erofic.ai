import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.db import crud
from app.engine.llm import LLMClient
from app.engine.processor import process_event
from app.engine.schema import LLMActionResponse, SpeakAction, ScheduleAction
from app.models import MessageRole


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
            {"type": "schedule", "content": "Delayed reply", "delay_seconds": 60},
        ]
    }
    resp = LLMActionResponse.model_validate(valid_json)
    assert len(resp.actions) == 2
    assert isinstance(resp.actions[0], SpeakAction)
    assert isinstance(resp.actions[1], ScheduleAction)
    assert resp.actions[1].delay_seconds == 60


@pytest.mark.asyncio
async def test_event_processor_execution(test_db: AsyncSession):
    session = await crud.create_session(test_db, system_prompt="Test Prompt")
    await crud.create_message(test_db, session.id, MessageRole.USER, "What is the status?")

    mock_llm = LLMClient()
    mock_llm.generate_actions = AsyncMock(
        return_value=LLMActionResponse(
            actions=[
                SpeakAction(content="Processing request"),
                ScheduleAction(content="Follow-up info", delay_seconds=120),
            ]
        )
    )

    result = await process_event(test_db, session.id, llm_client=mock_llm)
    assert result["status"] == "success"
    assert result["spoken"] == 1
    assert result["scheduled"] == 1

    messages = await crud.get_messages_for_session(test_db, session.id)
    assert len(messages) == 2
    assert messages[1].content == "Processing request"

    due_tasks = await crud.get_pending_tasks_due(test_db)
    assert len(due_tasks) == 0  # Delayed 120s, not due yet
