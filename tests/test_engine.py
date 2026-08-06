from datetime import datetime, timezone
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.db import crud
from app.engine.llm import LLMClient
from app.engine.processor import process_event
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
async def test_event_processor_execution(test_db: AsyncSession):
    session = await crud.create_session(test_db, system_prompt="Test Prompt")
    await crud.create_message(test_db, session.id, MessageRole.USER, "Hey there!")

    mock_llm = LLMClient()
    mock_llm.generate_actions = AsyncMock(
        return_value="This is a single assistant reply."
    )

    with patch("app.engine.processor.timer_manager.schedule_re_ping") as mock_schedule:
        result = await process_event(test_db, session.id, llm_client=mock_llm)
        assert result["status"] == "success"
        assert result["spoken"] == 1

    messages = await crud.get_messages_for_session(test_db, session.id)
    assert len(messages) == 2  # 1 user + 1 assistant
    assert messages[1].content == "This is a single assistant reply."


@pytest.mark.asyncio
async def test_default_30s_wakeup_timer_fallback(test_db: AsyncSession):
    session = await crud.create_session(test_db, system_prompt="Test Prompt")
    await crud.create_message(test_db, session.id, MessageRole.USER, "Just speak, no set_timer.")

    mock_llm = LLMClient()
    mock_llm.generate_actions = AsyncMock(
        return_value="Hello!"
    )

    with patch("app.engine.processor.timer_manager.schedule_re_ping") as mock_schedule:
        result = await process_event(test_db, session.id, llm_client=mock_llm)
        assert result["status"] == "success"
        assert result["timers_set"] == 0



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


def test_extract_json_from_text():
    from app.engine.llm import extract_json_from_text

    # 1. Clean JSON string
    assert extract_json_from_text('{"message": "Hello!"}')["message"] == "Hello!"

    # 2. Markdown codeblock wrapped JSON
    markdown_json = "```json\n{\n  \"message\": \"Markdown reply\"\n}\n```"
    assert extract_json_from_text(markdown_json)["message"] == "Markdown reply"

    # 3. Text commentary around JSON object
    commentary_json = "Here is the response: {\"message\": \"Inside braces\"} Hope this helps!"
    assert extract_json_from_text(commentary_json)["message"] == "Inside braces"

    # 4. Raw plain text fallback (not JSON)
    raw_plain_text = "I am an open weights model speaking plain text."
    assert extract_json_from_text(raw_plain_text)["message"] == "I am an open weights model speaking plain text."


