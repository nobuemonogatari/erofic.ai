import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    MessageCreateRequest,
    MessageResponse,
    SessionCreateRequest,
    SessionResponse,
    CharacterCreateRequest,
    CharacterUpdateRequest,
    CharacterResponse,
    SettingCreateRequest,
    SettingUpdateRequest,
    SettingResponse,
    RelationshipCreateRequest,
    RelationshipUpdateRequest,
    RelationshipResponse,
    StylePresetCreateRequest,
    StylePresetUpdateRequest,
    StylePresetResponse,
    SceneConfigCreateRequest,
    SceneConfigUpdateRequest,
    SceneConfigResponse,
    PrePackagedScenarioResponse,
)
from app.db import crud
from app.db.session import async_session_factory, get_async_session
from app.engine.processor import process_event
from app.models import MessageRole

logger = logging.getLogger(__name__)

router = APIRouter()


from app.engine.prompts import build_opening_scene_system_prompt


async def run_async_event_processor(session_id: str, trigger_type: str = "user_input"):
    async with async_session_factory() as db:
        try:
            logger.info(f"[BACKGROUND_TASK] Executing event processor for session {session_id} (trigger: {trigger_type})...")
            await process_event(db=db, session_id=session_id, trigger_type=trigger_type)
        except Exception as e:
            logger.error(f"[BACKGROUND_TASK] Error executing event processor for session {session_id}: {e}")


# --- Existing Session & Message Endpoints ---
@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session_endpoint(
    req: SessionCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
):
    system_prompt = req.system_prompt
    scene_config = None

    if req.scene_config_id:
        scene_config = await crud.get_scene_config(db, req.scene_config_id)
        if not scene_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scene configuration '{req.scene_config_id}' not found",
            )
        system_prompt = build_opening_scene_system_prompt(scene_config)

    session_obj = await crud.create_session(
        db, system_prompt=system_prompt, scene_config_id=req.scene_config_id
    )
    logger.info(f"[API] Created new chat session: {session_obj.id} (Bound Scene: {req.scene_config_id})")

    # If bound to a scenario, trigger opening scene beat generation automatically
    if req.scene_config_id:
        logger.info(f"[API] Dispatching background opening scene beat task for session {session_obj.id}")
        background_tasks.add_task(run_async_event_processor, session_obj.id, "scene_init")

    return session_obj



@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions_endpoint(
    db: AsyncSession = Depends(get_async_session),
):
    sessions = await crud.get_all_sessions(db)
    logger.debug(f"[API] Fetched {len(sessions)} session(s)")
    return sessions


@router.post("/sessions/{session_id}/message", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message_endpoint(
    session_id: str,
    req: MessageCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
):
    session_obj = await crud.get_session(db, session_id)
    if not session_obj:
        logger.warning(f"[API] POST message failed - Session {session_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    content = req.content.strip()

    # Multi-command parser for /phase <N>
    if "/phase" in content.lower() and session_obj.scene_config_id:
        import re
        phase_match = re.search(r"/phase\s+([1-3])", content, re.IGNORECASE)
        if phase_match:
            new_phase = int(phase_match.group(1))
            await crud.update_scene_config(db, session_obj.scene_config_id, current_phase=new_phase)
            logger.info(f"[API] Updated active phase to Phase {new_phase} for scene {session_obj.scene_config_id}")

    logger.info(f"[API] Received message for session {session_id}: '{content[:60]}...'")

    user_msg = await crud.create_message(
        db=db,
        session_id=session_id,
        role=MessageRole.USER,
        content=content,
    )

    logger.info(f"[API] Dispatched non-blocking background event processor task for session {session_id}")
    background_tasks.add_task(run_async_event_processor, session_id)

    return user_msg



@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages_endpoint(
    session_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    session_obj = await crud.get_session(db, session_id)
    if not session_obj:
        logger.warning(f"[API] GET messages failed - Session {session_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    messages = await crud.get_messages_for_session(db, session_id)
    logger.debug(f"[API] Fetched {len(messages)} message(s) for session {session_id}")
    return messages


# --- 1. Character Profiles CRUD Endpoints ---
@router.post("/api/characters", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character_endpoint(
    req: CharacterCreateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    return await crud.create_character(
        db=db,
        name=req.name,
        appearance=req.appearance,
        personality_and_voice=req.personality_and_voice,
        desires_and_dynamics=req.desires_and_dynamics,
        is_custom=req.is_custom,
    )


@router.get("/api/characters", response_model=list[CharacterResponse])
async def list_characters_endpoint(
    db: AsyncSession = Depends(get_async_session),
):
    return await crud.list_characters(db)


@router.get("/api/characters/{character_id}", response_model=CharacterResponse)
async def get_character_endpoint(
    character_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    char = await crud.get_character(db, character_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character profile not found")
    return char


@router.put("/api/characters/{character_id}", response_model=CharacterResponse)
async def update_character_endpoint(
    character_id: str,
    req: CharacterUpdateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    char = await crud.update_character(db, character_id, **req.model_dump(exclude_unset=True))
    if not char:
        raise HTTPException(status_code=404, detail="Character profile not found")
    return char


@router.delete("/api/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character_endpoint(
    character_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    success = await crud.delete_character(db, character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character profile not found")


# --- 2. Setting Presets CRUD Endpoints ---
@router.post("/api/settings", response_model=SettingResponse, status_code=status.HTTP_201_CREATED)
async def create_setting_endpoint(
    req: SettingCreateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    return await crud.create_setting(
        db=db,
        title=req.title,
        location_description=req.location_description,
        sensory_details=req.sensory_details,
        mood_tags=req.mood_tags,
        is_custom=req.is_custom,
    )


@router.get("/api/settings", response_model=list[SettingResponse])
async def list_settings_endpoint(
    db: AsyncSession = Depends(get_async_session),
):
    return await crud.list_settings(db)


@router.get("/api/settings/{setting_id}", response_model=SettingResponse)
async def get_setting_endpoint(
    setting_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    setting = await crud.get_setting(db, setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting preset not found")
    return setting


@router.put("/api/settings/{setting_id}", response_model=SettingResponse)
async def update_setting_endpoint(
    setting_id: str,
    req: SettingUpdateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    setting = await crud.update_setting(db, setting_id, **req.model_dump(exclude_unset=True))
    if not setting:
        raise HTTPException(status_code=404, detail="Setting preset not found")
    return setting


@router.delete("/api/settings/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting_endpoint(
    setting_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    success = await crud.delete_setting(db, setting_id)
    if not success:
        raise HTTPException(status_code=404, detail="Setting preset not found")


# --- 3. Relationship Dynamics CRUD Endpoints ---
@router.post("/api/relationships", response_model=RelationshipResponse, status_code=status.HTTP_201_CREATED)
async def create_relationship_endpoint(
    req: RelationshipCreateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    return await crud.create_relationship(
        db=db,
        name=req.name,
        history_description=req.history_description,
        power_dynamic=req.power_dynamic,
        current_tension=req.current_tension,
        is_custom=req.is_custom,
    )


@router.get("/api/relationships", response_model=list[RelationshipResponse])
async def list_relationships_endpoint(
    db: AsyncSession = Depends(get_async_session),
):
    return await crud.list_relationships(db)


@router.get("/api/relationships/{relationship_id}", response_model=RelationshipResponse)
async def get_relationship_endpoint(
    relationship_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    rel = await crud.get_relationship(db, relationship_id)
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship dynamic not found")
    return rel


@router.put("/api/relationships/{relationship_id}", response_model=RelationshipResponse)
async def update_relationship_endpoint(
    relationship_id: str,
    req: RelationshipUpdateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    rel = await crud.update_relationship(db, relationship_id, **req.model_dump(exclude_unset=True))
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship dynamic not found")
    return rel


@router.delete("/api/relationships/{relationship_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relationship_endpoint(
    relationship_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    success = await crud.delete_relationship(db, relationship_id)
    if not success:
        raise HTTPException(status_code=404, detail="Relationship dynamic not found")


# --- 4. Style & Tone Presets CRUD Endpoints ---
@router.post("/api/styles", response_model=StylePresetResponse, status_code=status.HTTP_201_CREATED)
async def create_style_endpoint(
    req: StylePresetCreateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    return await crud.create_style_preset(
        db=db,
        name=req.name,
        pacing=req.pacing,
        sensory_focus=req.sensory_focus,
        phase_1_prompt=req.phase_1_prompt,
        phase_2_prompt=req.phase_2_prompt,
        phase_3_prompt=req.phase_3_prompt,
        is_custom=req.is_custom,
    )


@router.get("/api/styles", response_model=list[StylePresetResponse])
async def list_styles_endpoint(
    db: AsyncSession = Depends(get_async_session),
):
    return await crud.list_style_presets(db)


@router.get("/api/styles/{style_id}", response_model=StylePresetResponse)
async def get_style_endpoint(
    style_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    style = await crud.get_style_preset(db, style_id)
    if not style:
        raise HTTPException(status_code=404, detail="Style preset not found")
    return style


@router.put("/api/styles/{style_id}", response_model=StylePresetResponse)
async def update_style_endpoint(
    style_id: str,
    req: StylePresetUpdateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    style = await crud.update_style_preset(db, style_id, **req.model_dump(exclude_unset=True))
    if not style:
        raise HTTPException(status_code=404, detail="Style preset not found")
    return style


@router.delete("/api/styles/{style_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_style_endpoint(
    style_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    success = await crud.delete_style_preset(db, style_id)
    if not success:
        raise HTTPException(status_code=404, detail="Style preset not found")


# --- 5. Scene Configurations & Scenarios Endpoints ---
@router.post("/api/scenes", response_model=SceneConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_scene_endpoint(
    req: SceneConfigCreateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    return await crud.create_scene_config(
        db=db,
        title=req.title,
        session_id=req.session_id,
        setting_id=req.setting_id,
        relationship_id=req.relationship_id,
        style_id=req.style_id,
        user_pov_character_id=req.user_pov_character_id,
        character_ids=req.character_ids,
        role_assignments=req.role_assignments,
        current_phase=req.current_phase,
        is_custom=req.is_custom,
    )



@router.get("/api/scenes", response_model=list[SceneConfigResponse])
async def list_scenes_endpoint(
    db: AsyncSession = Depends(get_async_session),
):
    return await crud.list_scene_configs(db)


@router.get("/api/scenarios/presets", response_model=list[PrePackagedScenarioResponse])
async def list_prepackaged_scenarios_endpoint(
    db: AsyncSession = Depends(get_async_session),
):
    # Fetch non-custom (pre-seeded) scene configs
    all_scenes = await crud.list_scene_configs(db)
    return [s for s in all_scenes if not s.is_custom]


@router.get("/api/scenes/{scene_id}", response_model=SceneConfigResponse)
async def get_scene_endpoint(
    scene_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    scene = await crud.get_scene_config(db, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene configuration not found")
    return scene


@router.put("/api/scenes/{scene_id}", response_model=SceneConfigResponse)
async def update_scene_endpoint(
    scene_id: str,
    req: SceneConfigUpdateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    scene = await crud.update_scene_config(
        db=db,
        scene_id=scene_id,
        character_ids=req.character_ids,
        **req.model_dump(exclude_unset=True, exclude={"character_ids"}),
    )
    if not scene:
        raise HTTPException(status_code=404, detail="Scene configuration not found")
    return scene


@router.delete("/api/scenes/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene_endpoint(
    scene_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    success = await crud.delete_scene_config(db, scene_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scene configuration not found")


from app.api.schemas import OpeningScenePreviewResponse
from app.engine.llm import LLMClient, SYSTEM_JSON_INSTRUCTION

@router.post("/api/scenes/{scene_id}/generate-opening", response_model=OpeningScenePreviewResponse)
async def generate_opening_scene_endpoint(
    scene_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    scene = await crud.get_scene_config(db, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene configuration not found")

    compiled_prompt = build_opening_scene_system_prompt(scene)
    llm_payload = [
        {"role": "system", "content": SYSTEM_JSON_INSTRUCTION.format(persona_guidelines=f"3. {compiled_prompt}")}
    ]

    client = LLMClient()
    try:
        opening_beat = await client.generate_actions(
            llm_payload, temperature=0.85, max_tokens=250
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {e}")




    return OpeningScenePreviewResponse(
        scene_config_id=scene_id,
        system_prompt_compiled=compiled_prompt,
        generated_opening_beat=opening_beat,
    )



async def trigger_re_ping(session_id: str):
    async with async_session_factory() as db:
        try:
            logger.info(f"[API] Executing in-memory re-ping event processor for session {session_id}...")
            await process_event(db=db, session_id=session_id, trigger_type="scheduled_action")
        except Exception as e:
            logger.error(f"[API] Error executing re-ping event processor for session {session_id}: {e}")
