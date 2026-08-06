from datetime import datetime, timezone
import uuid

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    scene_config_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("scene_configs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    scene_config: Mapped["SceneConfigModel | None"] = relationship(
        "SceneConfigModel", foreign_keys=[scene_config_id]
    )
    messages: Mapped[list["MessageModel"]] = relationship(
        "MessageModel", back_populates="session", cascade="all, delete-orphan"
    )



