from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MessageRole
from app.models.session import SessionModel
from app.models.message import MessageModel


async def create_session(
    db: AsyncSession, system_prompt: str = ""
) -> SessionModel:
    session_obj = SessionModel(system_prompt=system_prompt)
    db.add(session_obj)
    await db.commit()
    await db.refresh(session_obj)
    return session_obj


async def get_session(
    db: AsyncSession, session_id: str
) -> SessionModel | None:
    result = await db.execute(
        select(SessionModel).where(SessionModel.id == session_id)
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


# Database-backed task CRUD operations removed in favor of in-memory TimerManager.
