import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
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
async def test_character_crud(test_db: AsyncSession):
    # 1. Create
    char = await crud.create_character(
        test_db,
        name="Julian",
        appearance="Dark hair",
        personality_and_voice="Husky voice",
        desires_and_dynamics="Teasing",
    )
    assert char.id is not None
    assert char.name == "Julian"

    # 2. Read
    fetched = await crud.get_character(test_db, char.id)
    assert fetched is not None
    assert fetched.name == "Julian"

    # 3. Update
    updated = await crud.update_character(test_db, char.id, name="Julian Vance")
    assert updated is not None
    assert updated.name == "Julian Vance"

    # 4. List
    chars = await crud.list_characters(test_db)
    assert len(chars) == 1

    # 5. Delete
    deleted = await crud.delete_character(test_db, char.id)
    assert deleted is True
    assert await crud.get_character(test_db, char.id) is None


@pytest.mark.asyncio
async def test_setting_crud(test_db: AsyncSession):
    setting = await crud.create_setting(test_db, title="Penthouse", mood_tags="intimate")
    assert setting.id is not None
    assert setting.title == "Penthouse"

    settings = await crud.list_settings(test_db)
    assert len(settings) == 1

    deleted = await crud.delete_setting(test_db, setting.id)
    assert deleted is True


@pytest.mark.asyncio
async def test_relationship_crud(test_db: AsyncSession):
    rel = await crud.create_relationship(test_db, name="Exes", power_dynamic="Equal")
    assert rel.id is not None
    assert rel.name == "Exes"

    rels = await crud.list_relationships(test_db)
    assert len(rels) == 1

    deleted = await crud.delete_relationship(test_db, rel.id)
    assert deleted is True


@pytest.mark.asyncio
async def test_style_crud(test_db: AsyncSession):
    style = await crud.create_style_preset(test_db, name="Slow Burn", pacing="Gradual")
    assert style.id is not None
    assert style.name == "Slow Burn"

    styles = await crud.list_style_presets(test_db)
    assert len(styles) == 1

    deleted = await crud.delete_style_preset(test_db, style.id)
    assert deleted is True


@pytest.mark.asyncio
async def test_scene_config_crud(test_db: AsyncSession):
    char1 = await crud.create_character(test_db, name="Julian")
    char2 = await crud.create_character(test_db, name="Elena")
    setting = await crud.create_setting(test_db, title="Cabin")
    rel = await crud.create_relationship(test_db, name="Rivals")
    style = await crud.create_style_preset(test_db, name="Intense")

    scene = await crud.create_scene_config(
        test_db,
        title="Cabin Encounter",
        setting_id=setting.id,
        relationship_id=rel.id,
        style_id=style.id,
        user_pov_character_id=char1.id,
        character_ids=[char1.id, char2.id],
    )

    assert scene.id is not None
    assert scene.title == "Cabin Encounter"
    assert scene.setting.title == "Cabin"
    assert scene.relationship_dynamic.name == "Rivals"
    assert scene.style.name == "Intense"
    assert scene.user_pov_character.name == "Julian"
    assert len(scene.characters) == 2

    # Update scene
    updated = await crud.update_scene_config(test_db, scene.id, title="Midnight Encounter")
    assert updated.title == "Midnight Encounter"

    # Delete scene
    deleted = await crud.delete_scene_config(test_db, scene.id)
    assert deleted is True
