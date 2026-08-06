import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.db import crud
from app.db.seed import seed_database
from app.engine.prompts import build_opening_scene_system_prompt


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
async def test_session_scenario_binding_and_opening_prompt(test_db: AsyncSession):
    # Seed library data
    await seed_database(test_db)

    # Get a pre-packaged scenario
    scenarios = await crud.list_scene_configs(test_db)
    assert len(scenarios) >= 1
    scenario = scenarios[0]

    # Create session bound to this scenario
    session = await crud.create_session(test_db, scene_config_id=scenario.id)
    assert session.scene_config_id == scenario.id
    assert session.scene_config is not None
    assert session.scene_config.title == scenario.title

    # Test prompt compilation
    prompt = build_opening_scene_system_prompt(session.scene_config)
    assert "SCENE CONFIGURATION" in prompt
    assert "INSTRUCTIONS FOR THE OPENING SCENE ACTION BEAT" in prompt
    assert "STRICT USER AUTONOMY & AGENCY GUARDRAILS" in prompt
    assert "Phase 1" in prompt



