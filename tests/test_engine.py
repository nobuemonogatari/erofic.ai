from datetime import datetime, timezone
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.db import crud
from app.engine.llm import LLMClient
from app.engine.processor import process_event
from app.engine.schema import LLMActionResponse, SpeakAction
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
        ]
    }
    resp = LLMActionResponse.model_validate(valid_json)
    assert len(resp.actions) == 1
    assert isinstance(resp.actions[0], SpeakAction)


@pytest.mark.asyncio
async def test_multiple_sequential_speak_actions(test_db: AsyncSession):
    session = await crud.create_session(test_db, system_prompt="Test Prompt")
    await crud.create_message(test_db, session.id, MessageRole.USER, "Tell me a story in parts.")

    mock_llm = LLMClient()
    mock_llm.generate_actions = AsyncMock(
        return_value=LLMActionResponse(
            actions=[
                SpeakAction(content="Part 1: Once upon a time..."),
                SpeakAction(content="Part 2: There was a coder..."),
                SpeakAction(content="Part 3: Who built great AI systems."),
            ]
        )
    )

    with patch("app.engine.processor.timer_manager.schedule_re_ping") as mock_schedule:
        result = await process_event(test_db, session.id, llm_client=mock_llm)
        assert result["status"] == "success"
        assert result["spoken"] == 3
        mock_schedule.assert_called_once_with(session.id, delay=30)

    messages = await crud.get_messages_for_session(test_db, session.id)
    assert len(messages) == 4  # 1 user + 3 assistant
    assert messages[1].content == "Part 1: Once upon a time..."
    assert messages[2].content == "Part 2: There was a coder..."
    assert messages[3].content == "Part 3: Who built great AI systems."


@pytest.mark.asyncio
async def test_default_30s_wakeup_timer_fallback(test_db: AsyncSession):
    session = await crud.create_session(test_db, system_prompt="Test Prompt")
    await crud.create_message(test_db, session.id, MessageRole.USER, "Just speak, no set_timer.")

    mock_llm = LLMClient()
    mock_llm.generate_actions = AsyncMock(
        return_value=LLMActionResponse(
            actions=[SpeakAction(content="Hello!")]
        )
    )

    with patch("app.engine.processor.timer_manager.schedule_re_ping") as mock_schedule:
        result = await process_event(test_db, session.id, llm_client=mock_llm)
        assert result["status"] == "success"
        assert result["timers_set"] == 1
        mock_schedule.assert_called_once_with(session.id, delay=30)


@pytest.mark.asyncio
async def test_llm_failure_10s_error_retry_timer(test_db: AsyncSession):
    from app.engine.llm import LLMGenerationError

    session = await crud.create_session(test_db, system_prompt="Test Prompt")
    await crud.create_message(test_db, session.id, MessageRole.USER, "Test LLM error handling")

    mock_llm = LLMClient()
    mock_llm.generate_actions = AsyncMock(
        side_effect=LLMGenerationError("Simulated API failure")
    )

    with patch("app.engine.processor.timer_manager.schedule_re_ping") as mock_schedule:
        result = await process_event(test_db, session.id, llm_client=mock_llm)
        assert result["status"] == "error"
        assert result["timers_set"] == 1
        mock_schedule.assert_called_once_with(session.id, delay=10)
