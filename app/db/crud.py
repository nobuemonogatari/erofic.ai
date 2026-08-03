from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MessageRole, TaskStatus
from app.models.session import SessionModel
from app.models.message import MessageModel
from app.models.task import ScheduledTaskModel


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


async def create_scheduled_task(
    db: AsyncSession, session_id: str, execute_at: datetime
) -> ScheduledTaskModel:
    task_obj = ScheduledTaskModel(
        session_id=session_id,
        execute_at=execute_at,
        status=TaskStatus.PENDING,
    )
    db.add(task_obj)
    await db.commit()
    await db.refresh(task_obj)
    return task_obj


async def get_scheduled_task(
    db: AsyncSession, task_id: str
) -> ScheduledTaskModel | None:
    result = await db.execute(
        select(ScheduledTaskModel).where(ScheduledTaskModel.id == task_id)
    )
    return result.scalar_one_or_none()


async def get_pending_tasks_due(
    db: AsyncSession, now: datetime | None = None
) -> Sequence[ScheduledTaskModel]:
    current_time = now or datetime.now(timezone.utc)
    result = await db.execute(
        select(ScheduledTaskModel)
        .where(
            ScheduledTaskModel.status == TaskStatus.PENDING,
            ScheduledTaskModel.execute_at <= current_time,
        )
        .order_by(ScheduledTaskModel.execute_at.asc())
    )
    return result.scalars().all()


async def mark_task_status(
    db: AsyncSession, task_id: str, status: TaskStatus
) -> ScheduledTaskModel | None:
    task = await get_scheduled_task(db, task_id)
    if task:
        task.status = status
        await db.commit()
        await db.refresh(task)
    return task


async def cancel_pending_tasks_for_session(
    db: AsyncSession, session_id: str
) -> int:
    result = await db.execute(
        select(ScheduledTaskModel).where(
            ScheduledTaskModel.session_id == session_id,
            ScheduledTaskModel.status == TaskStatus.PENDING,
        )
    )
    pending_tasks = result.scalars().all()
    count = 0
    for task in pending_tasks:
        task.status = TaskStatus.CANCELLED
        count += 1
    if count > 0:
        await db.commit()
    return count
