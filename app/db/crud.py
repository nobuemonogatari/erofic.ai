from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    MessageRole,
    SessionModel,
    MessageModel,
    CharacterProfileModel,
    SettingPresetModel,
    RelationshipDynamicModel,
    StyleAndTonePresetModel,
    SceneConfigModel,
)


# --- Existing Session & Message CRUD ---
async def create_session(
    db: AsyncSession, system_prompt: str = "", scene_config_id: str | None = None
) -> SessionModel:
    session_obj = SessionModel(system_prompt=system_prompt, scene_config_id=scene_config_id)
    db.add(session_obj)
    await db.commit()
    return await get_session(db, session_obj.id)


async def get_session(
    db: AsyncSession, session_id: str
) -> SessionModel | None:
    result = await db.execute(
        select(SessionModel)
        .options(
            selectinload(SessionModel.scene_config).selectinload(SceneConfigModel.setting),
            selectinload(SessionModel.scene_config).selectinload(SceneConfigModel.relationship_dynamic),
            selectinload(SessionModel.scene_config).selectinload(SceneConfigModel.style),
            selectinload(SessionModel.scene_config).selectinload(SceneConfigModel.user_pov_character),
            selectinload(SessionModel.scene_config).selectinload(SceneConfigModel.characters),
        )
        .where(SessionModel.id == session_id)
    )
    return result.scalar_one_or_none()



async def get_all_sessions(
    db: AsyncSession
) -> Sequence[SessionModel]:
    result = await db.execute(
        select(SessionModel).order_by(SessionModel.created_at.desc())
    )
    return result.scalars().all()


async def create_message(
    db: AsyncSession,
    session_id: str,
    role: MessageRole,
    content: str,
    timestamp: datetime | None = None,
) -> MessageModel:
    message_obj = MessageModel(
        session_id=session_id,
        role=role,
        content=content,
        timestamp=timestamp or datetime.now(timezone.utc),
    )
    db.add(message_obj)
    await db.commit()
    await db.refresh(message_obj)
    return message_obj


async def get_messages_for_session(
    db: AsyncSession, session_id: str
) -> Sequence[MessageModel]:
    result = await db.execute(
        select(MessageModel)
        .where(MessageModel.session_id == session_id)
        .order_by(MessageModel.timestamp.asc())
    )
    return result.scalars().all()


# --- Character CRUD ---
async def create_character(
    db: AsyncSession,
    name: str,
    appearance: str = "",
    personality_and_voice: str = "",
    desires_and_dynamics: str = "",
    is_custom: bool = True,
) -> CharacterProfileModel:
    character = CharacterProfileModel(
        name=name,
        appearance=appearance,
        personality_and_voice=personality_and_voice,
        desires_and_dynamics=desires_and_dynamics,
        is_custom=is_custom,
    )
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character


async def get_character(
    db: AsyncSession, character_id: str
) -> CharacterProfileModel | None:
    result = await db.execute(
        select(CharacterProfileModel).where(CharacterProfileModel.id == character_id)
    )
    return result.scalar_one_or_none()


async def list_characters(
    db: AsyncSession
) -> Sequence[CharacterProfileModel]:
    result = await db.execute(
        select(CharacterProfileModel).order_by(CharacterProfileModel.created_at.desc())
    )
    return result.scalars().all()


async def update_character(
    db: AsyncSession,
    character_id: str,
    **kwargs,
) -> CharacterProfileModel | None:
    character = await get_character(db, character_id)
    if not character:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(character, key):
            setattr(character, key, value)
    await db.commit()
    await db.refresh(character)
    return character


async def delete_character(
    db: AsyncSession, character_id: str
) -> bool:
    character = await get_character(db, character_id)
    if not character:
        return False
    await db.delete(character)
    await db.commit()
    return True


# --- Setting CRUD ---
async def create_setting(
    db: AsyncSession,
    title: str,
    location_description: str = "",
    sensory_details: str = "",
    mood_tags: str = "",
    is_custom: bool = True,
) -> SettingPresetModel:
    setting = SettingPresetModel(
        title=title,
        location_description=location_description,
        sensory_details=sensory_details,
        mood_tags=mood_tags,
        is_custom=is_custom,
    )
    db.add(setting)
    await db.commit()
    await db.refresh(setting)
    return setting


async def get_setting(
    db: AsyncSession, setting_id: str
) -> SettingPresetModel | None:
    result = await db.execute(
        select(SettingPresetModel).where(SettingPresetModel.id == setting_id)
    )
    return result.scalar_one_or_none()


async def list_settings(
    db: AsyncSession
) -> Sequence[SettingPresetModel]:
    result = await db.execute(
        select(SettingPresetModel).order_by(SettingPresetModel.created_at.desc())
    )
    return result.scalars().all()


async def update_setting(
    db: AsyncSession,
    setting_id: str,
    **kwargs,
) -> SettingPresetModel | None:
    setting = await get_setting(db, setting_id)
    if not setting:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(setting, key):
            setattr(setting, key, value)
    await db.commit()
    await db.refresh(setting)
    return setting


async def delete_setting(
    db: AsyncSession, setting_id: str
) -> bool:
    setting = await get_setting(db, setting_id)
    if not setting:
        return False
    await db.delete(setting)
    await db.commit()
    return True


# --- Relationship Dynamic CRUD ---
async def create_relationship(
    db: AsyncSession,
    name: str,
    history_description: str = "",
    power_dynamic: str = "",
    current_tension: str = "",
    is_custom: bool = True,
) -> RelationshipDynamicModel:
    rel = RelationshipDynamicModel(
        name=name,
        history_description=history_description,
        power_dynamic=power_dynamic,
        current_tension=current_tension,
        is_custom=is_custom,
    )
    db.add(rel)
    await db.commit()
    await db.refresh(rel)
    return rel


async def get_relationship(
    db: AsyncSession, relationship_id: str
) -> RelationshipDynamicModel | None:
    result = await db.execute(
        select(RelationshipDynamicModel).where(RelationshipDynamicModel.id == relationship_id)
    )
    return result.scalar_one_or_none()


async def list_relationships(
    db: AsyncSession
) -> Sequence[RelationshipDynamicModel]:
    result = await db.execute(
        select(RelationshipDynamicModel).order_by(RelationshipDynamicModel.created_at.desc())
    )
    return result.scalars().all()


async def update_relationship(
    db: AsyncSession,
    relationship_id: str,
    **kwargs,
) -> RelationshipDynamicModel | None:
    rel = await get_relationship(db, relationship_id)
    if not rel:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(rel, key):
            setattr(rel, key, value)
    await db.commit()
    await db.refresh(rel)
    return rel


async def delete_relationship(
    db: AsyncSession, relationship_id: str
) -> bool:
    rel = await get_relationship(db, relationship_id)
    if not rel:
        return False
    await db.delete(rel)
    await db.commit()
    return True


# --- Style Preset CRUD ---
async def create_style_preset(
    db: AsyncSession,
    name: str,
    pacing: str = "",
    sensory_focus: str = "",
    phase_1_prompt: str = "",
    phase_2_prompt: str = "",
    phase_3_prompt: str = "",
    is_custom: bool = True,
) -> StyleAndTonePresetModel:
    style = StyleAndTonePresetModel(
        name=name,
        pacing=pacing,
        sensory_focus=sensory_focus,
        phase_1_prompt=phase_1_prompt,
        phase_2_prompt=phase_2_prompt,
        phase_3_prompt=phase_3_prompt,
        is_custom=is_custom,
    )
    db.add(style)
    await db.commit()
    await db.refresh(style)
    return style


async def get_style_preset(
    db: AsyncSession, style_id: str
) -> StyleAndTonePresetModel | None:
    result = await db.execute(
        select(StyleAndTonePresetModel).where(StyleAndTonePresetModel.id == style_id)
    )
    return result.scalar_one_or_none()


async def list_style_presets(
    db: AsyncSession
) -> Sequence[StyleAndTonePresetModel]:
    result = await db.execute(
        select(StyleAndTonePresetModel).order_by(StyleAndTonePresetModel.created_at.desc())
    )
    return result.scalars().all()


async def update_style_preset(
    db: AsyncSession,
    style_id: str,
    **kwargs,
) -> StyleAndTonePresetModel | None:
    style = await get_style_preset(db, style_id)
    if not style:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(style, key):
            setattr(style, key, value)
    await db.commit()
    await db.refresh(style)
    return style


async def delete_style_preset(
    db: AsyncSession, style_id: str
) -> bool:
    style = await get_style_preset(db, style_id)
    if not style:
        return False
    await db.delete(style)
    await db.commit()
    return True


import json

# --- Scene Config CRUD ---
async def create_scene_config(
    db: AsyncSession,
    title: str = "Untitled Scene",
    session_id: str | None = None,
    setting_id: str | None = None,
    relationship_id: str | None = None,
    style_id: str | None = None,
    user_pov_character_id: str | None = None,
    character_ids: list[str] | None = None,
    role_assignments: dict[str, str] | None = None,
    current_phase: int = 1,
    is_custom: bool = True,
) -> SceneConfigModel:
    role_str = json.dumps(role_assignments or {})
    scene = SceneConfigModel(
        title=title,
        session_id=session_id,
        setting_id=setting_id,
        relationship_id=relationship_id,
        style_id=style_id,
        user_pov_character_id=user_pov_character_id,
        role_assignments=role_str,
        current_phase=current_phase,
        is_custom=is_custom,
    )


    if character_ids:
        chars_res = await db.execute(
            select(CharacterProfileModel).where(CharacterProfileModel.id.in_(character_ids))
        )
        scene.characters = list(chars_res.scalars().all())

    db.add(scene)
    await db.commit()
    return await get_scene_config(db, scene.id)


async def get_scene_config(
    db: AsyncSession, scene_id: str
) -> SceneConfigModel | None:
    result = await db.execute(
        select(SceneConfigModel)
        .options(
            selectinload(SceneConfigModel.setting),
            selectinload(SceneConfigModel.relationship_dynamic),
            selectinload(SceneConfigModel.style),
            selectinload(SceneConfigModel.user_pov_character),
            selectinload(SceneConfigModel.characters),
        )
        .where(SceneConfigModel.id == scene_id)
    )
    scene = result.scalar_one_or_none()
    if scene and isinstance(scene.role_assignments, str):
        try:
            # Parse for Pydantic response compatibility using dict attribute
            parsed = json.loads(scene.role_assignments)
            object.__setattr__(scene, "parsed_role_assignments", parsed)
        except Exception:
            object.__setattr__(scene, "parsed_role_assignments", {})
    return scene



async def list_scene_configs(
    db: AsyncSession
) -> Sequence[SceneConfigModel]:
    result = await db.execute(
        select(SceneConfigModel)
        .options(
            selectinload(SceneConfigModel.setting),
            selectinload(SceneConfigModel.relationship_dynamic),
            selectinload(SceneConfigModel.style),
            selectinload(SceneConfigModel.user_pov_character),
            selectinload(SceneConfigModel.characters),
        )
        .order_by(SceneConfigModel.created_at.desc())
    )
    scenes = result.scalars().all()
    for s in scenes:
        if isinstance(s.role_assignments, str):
            try:
                parsed = json.loads(s.role_assignments)
                object.__setattr__(s, "parsed_role_assignments", parsed)
            except Exception:
                object.__setattr__(s, "parsed_role_assignments", {})
    return scenes



async def update_scene_config(
    db: AsyncSession,
    scene_id: str,
    character_ids: list[str] | None = None,
    role_assignments: dict[str, str] | None = None,
    **kwargs,
) -> SceneConfigModel | None:
    scene = await get_scene_config(db, scene_id)
    if not scene:
        return None

    if role_assignments is not None:
        kwargs["role_assignments"] = json.dumps(role_assignments)

    for key, value in kwargs.items():
        if value is not None and hasattr(scene, key):
            setattr(scene, key, value)

    if character_ids is not None:
        chars_res = await db.execute(
            select(CharacterProfileModel).where(CharacterProfileModel.id.in_(character_ids))
        )
        scene.characters = list(chars_res.scalars().all())

    await db.commit()
    return await get_scene_config(db, scene.id)



async def delete_scene_config(
    db: AsyncSession, scene_id: str
) -> bool:
    scene = await get_scene_config(db, scene_id)
    if not scene:
        return False
    await db.delete(scene)
    await db.commit()
    return True
