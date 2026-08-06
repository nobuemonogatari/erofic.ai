from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models import MessageRole


# Existing Session & Message Schemas
class SessionCreateRequest(BaseModel):
    system_prompt: str = ""


class SessionResponse(BaseModel):
    id: str
    system_prompt: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageCreateRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: MessageRole
    content: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Scene Component Schemas ---

# 1. Character Schemas
class CharacterCreateRequest(BaseModel):
    name: str
    appearance: str = ""
    personality_and_voice: str = ""
    desires_and_dynamics: str = ""
    is_custom: bool = True


class CharacterUpdateRequest(BaseModel):
    name: str | None = None
    appearance: str | None = None
    personality_and_voice: str | None = None
    desires_and_dynamics: str | None = None
    is_custom: bool | None = None


class CharacterResponse(BaseModel):
    id: str
    name: str
    appearance: str
    personality_and_voice: str
    desires_and_dynamics: str
    is_custom: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 2. Setting Schemas
class SettingCreateRequest(BaseModel):
    title: str
    location_description: str = ""
    sensory_details: str = ""
    mood_tags: str = ""
    is_custom: bool = True


class SettingUpdateRequest(BaseModel):
    title: str | None = None
    location_description: str | None = None
    sensory_details: str | None = None
    mood_tags: str | None = None
    is_custom: bool | None = None


class SettingResponse(BaseModel):
    id: str
    title: str
    location_description: str
    sensory_details: str
    mood_tags: str
    is_custom: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 3. Relationship Schemas
class RelationshipCreateRequest(BaseModel):
    name: str
    history_description: str = ""
    power_dynamic: str = ""
    current_tension: str = ""
    is_custom: bool = True


class RelationshipUpdateRequest(BaseModel):
    name: str | None = None
    history_description: str | None = None
    power_dynamic: str | None = None
    current_tension: str | None = None
    is_custom: bool | None = None


class RelationshipResponse(BaseModel):
    id: str
    name: str
    history_description: str
    power_dynamic: str
    current_tension: str
    is_custom: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 4. Style Schemas
class StylePresetCreateRequest(BaseModel):
    name: str
    pacing: str = ""
    sensory_focus: str = ""
    phase_1_prompt: str = ""
    phase_2_prompt: str = ""
    phase_3_prompt: str = ""
    is_custom: bool = True


class StylePresetUpdateRequest(BaseModel):
    name: str | None = None
    pacing: str | None = None
    sensory_focus: str | None = None
    phase_1_prompt: str | None = None
    phase_2_prompt: str | None = None
    phase_3_prompt: str | None = None
    is_custom: bool | None = None


class StylePresetResponse(BaseModel):
    id: str
    name: str
    pacing: str
    sensory_focus: str
    phase_1_prompt: str
    phase_2_prompt: str
    phase_3_prompt: str
    is_custom: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 5. Scene Config Schemas
class SceneConfigCreateRequest(BaseModel):
    title: str = "Untitled Scene"
    session_id: str | None = None
    setting_id: str | None = None
    relationship_id: str | None = None
    style_id: str | None = None
    user_pov_character_id: str | None = None
    character_ids: list[str] = []
    role_assignments: dict[str, str] = {}
    current_phase: int = 1
    is_custom: bool = True


class SceneConfigUpdateRequest(BaseModel):
    title: str | None = None
    session_id: str | None = None
    setting_id: str | None = None
    relationship_id: str | None = None
    style_id: str | None = None
    user_pov_character_id: str | None = None
    character_ids: list[str] | None = None
    role_assignments: dict[str, str] | None = None
    current_phase: int | None = None
    is_custom: bool | None = None


class SceneConfigResponse(BaseModel):
    id: str
    session_id: str | None
    title: str
    setting_id: str | None
    relationship_id: str | None
    style_id: str | None
    user_pov_character_id: str | None
    role_assignments: dict[str, str] = {}
    current_phase: int = 1
    is_custom: bool
    created_at: datetime
    updated_at: datetime

    setting: SettingResponse | None = None
    relationship_dynamic: RelationshipResponse | None = None
    style: StylePresetResponse | None = None
    user_pov_character: CharacterResponse | None = None
    characters: list[CharacterResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PrePackagedScenarioResponse(BaseModel):
    id: str
    title: str
    role_assignments: dict[str, str] = {}
    current_phase: int = 1
    setting: SettingResponse | None = None
    relationship_dynamic: RelationshipResponse | None = None
    style: StylePresetResponse | None = None
    user_pov_character: CharacterResponse | None = None
    characters: list[CharacterResponse] = []

    model_config = ConfigDict(from_attributes=True)


