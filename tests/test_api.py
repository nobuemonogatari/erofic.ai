from unittest.mock import AsyncMock, patch
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.db.session import get_async_session
from app.engine.schema import LLMActionResponse, SpeakAction
from app.main import app


@pytest_asyncio.fixture
async def async_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_db

    with patch("app.api.routes.async_session_factory", session_factory):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}


@pytest.mark.asyncio
async def test_sessions_and_messages_endpoints(async_client: AsyncClient):
    # 1. Create Session
    create_res = await async_client.post(
        "/sessions", json={"system_prompt": "API Test Prompt"}
    )
    assert create_res.status_code == 201
    session_data = create_res.json()
    session_id = session_data["id"]
    assert session_data["system_prompt"] == "API Test Prompt"

    # List Sessions
    list_res = await async_client.get("/sessions")
    assert list_res.status_code == 200
    sessions_list = list_res.json()
    assert len(sessions_list) >= 1
    assert any(s["id"] == session_id for s in sessions_list)

    # 2. Post User Message (mock LLM response)
    with patch(
        "app.engine.processor.LLMClient.generate_actions",
        new_callable=AsyncMock,
        return_value=LLMActionResponse(
            actions=[SpeakAction(content="Bot reply via API")]
        ),
    ):
        msg_res = await async_client.post(
            f"/sessions/{session_id}/message", json={"content": "Hello bot!"}
        )
        assert msg_res.status_code == 201
        msg_data = msg_res.json()
        assert msg_data["role"] == "user"
        assert msg_data["content"] == "Hello bot!"

    # 3. Get Messages
    get_res = await async_client.get(f"/sessions/{session_id}/messages")
    assert get_res.status_code == 200
    messages = get_res.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello bot!"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Bot reply via API"
