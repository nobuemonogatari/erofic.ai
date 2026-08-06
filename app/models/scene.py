from datetime import datetime, timezone
import uuid
import json


from sqlalchemy import String, Text, DateTime, Boolean, Integer, ForeignKey, Table, Column

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CharacterProfileModel(Base):
    __tablename__ = "character_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    appearance: Mapped[str] = mapped_column(Text, nullable=False, default="")
    personality_and_voice: Mapped[str] = mapped_column(Text, nullable=False, default="")
    desires_and_dynamics: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class SettingPresetModel(Base):
    __tablename__ = "setting_presets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sensory_details: Mapped[str] = mapped_column(Text, nullable=False, default="")
    mood_tags: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class RelationshipDynamicModel(Base):
    __tablename__ = "relationship_dynamics"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    history_description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    power_dynamic: Mapped[str] = mapped_column(Text, nullable=False, default="")
    current_tension: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class StyleAndTonePresetModel(Base):
    __tablename__ = "style_presets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    pacing: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sensory_focus: Mapped[str] = mapped_column(Text, nullable=False, default="")
    phase_1_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    phase_2_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    phase_3_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


# Junction Table for SceneConfig <-> CharacterProfile
scene_character_link = Table(
    "scene_character_links",
    Base.metadata,
    Column("scene_config_id", String(36), ForeignKey("scene_configs.id", ondelete="CASCADE"), primary_key=True),
    Column("character_id", String(36), ForeignKey("character_profiles.id", ondelete="CASCADE"), primary_key=True),
)


class SceneConfigModel(Base):
    __tablename__ = "scene_configs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="Untitled Scene")
    setting_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("setting_presets.id", ondelete="SET NULL"), nullable=True
    )
    relationship_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("relationship_dynamics.id", ondelete="SET NULL"), nullable=True
    )
    style_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("style_presets.id", ondelete="SET NULL"), nullable=True
    )
    user_pov_character_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("character_profiles.id", ondelete="SET NULL"), nullable=True
    )
    role_assignments: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    current_phase: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


    @property
    def role_assignments_dict(self) -> dict[str, str]:
        if not self.role_assignments:
            return {}
        try:
            return json.loads(self.role_assignments)
        except Exception:
            return {}



    # Relationships
    setting = relationship("SettingPresetModel")
    relationship_dynamic = relationship("RelationshipDynamicModel")
    style = relationship("StyleAndTonePresetModel")
    user_pov_character = relationship(
        "CharacterProfileModel", foreign_keys=[user_pov_character_id]
    )
    characters = relationship(
        "CharacterProfileModel", secondary=scene_character_link
    )


