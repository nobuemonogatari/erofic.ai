import enum


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


from app.models.session import SessionModel
from app.models.message import MessageModel
from app.models.scene import (
    CharacterProfileModel,
    SettingPresetModel,
    RelationshipDynamicModel,
    StyleAndTonePresetModel,
    SceneConfigModel,
    scene_character_link,
)

__all__ = [
    "MessageRole",
    "SessionModel",
    "MessageModel",
    "CharacterProfileModel",
    "SettingPresetModel",
    "RelationshipDynamicModel",
    "StyleAndTonePresetModel",
    "SceneConfigModel",
    "scene_character_link",
]



