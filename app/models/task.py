from datetime import datetime, timezone
import uuid

from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models import TaskStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ScheduledTaskModel(Base):
    __tablename__ = "scheduled_tasks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execute_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, native_enum=False), default=TaskStatus.PENDING, nullable=False, index=True
    )

    session: Mapped["SessionModel"] = relationship("SessionModel", back_populates="scheduled_tasks")
