import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.db.seed import seed_database
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
async def test_seed_database(test_db: AsyncSession):
    # Run seed script
    await seed_database(test_db)

    # 1. Verify Characters
    chars = await crud.list_characters(test_db)
    char_names = {c.name for c in chars}
    assert "Koyomi" in char_names
    assert "Shinobu" in char_names
    assert "Hitagi" in char_names

    # 2. Verify Settings
    settings = await crud.list_settings(test_db)
    setting_titles = {s.title for s in settings}
    assert "Koyomi's Bedroom" in setting_titles
    assert "Hitagi's Apartment Room" in setting_titles

    # 3. Verify Relationships
    rels = await crud.list_relationships(test_db)
    rel_names = {r.name for r in rels}
    assert "Master & Servant (Playful Roleplay)" in rel_names
    assert "Dominant & Possessive Attachment" in rel_names

    # 4. Verify Style Presets
    styles = await crud.list_style_presets(test_db)
    style_names = {s.name for s in styles}
    assert "3-Phase Seductive Escalation" in style_names
    assert styles[0].phase_1_prompt != ""
    assert styles[0].phase_2_prompt != ""
    assert styles[0].phase_3_prompt != ""

    # 5. Verify Pre-Packaged Scenarios
    scenes = await crud.list_scene_configs(test_db)
    assert len(scenes) == 2
    scenario_titles = {s.title for s in scenes}
    assert "Shinobu's Master & Servant Play" in scenario_titles
    assert "Hitagi's Apartment Encounter" in scenario_titles
