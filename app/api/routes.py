import logging
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    MessageCreateRequest,
    MessageResponse,
    SessionCreateRequest,
    SessionResponse,
)
from app.db import crud
from app.db.session import async_session_factory, get_async_session
from app.engine.processor import process_event
from app.models import MessageRole

logger = logging.getLogger(__name__)

router = APIRouter()


async def run_async_event_processor(session_id: str):
    async with async_session_factory() as db:
        try:
            logger.info(f"[BACKGROUND_TASK] Executing event processor for session {session_id}...")
            await process_event(db=db, session_id=session_id, trigger_type="user_input")
        except Exception as e:
            logger.error(f"[BACKGROUND_TASK] Error executing event processor for session {session_id}: {e}")


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session_endpoint(
    req: SessionCreateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    session_obj = await crud.create_session(db, system_prompt=req.system_prompt)
    logger.info(f"[API] Created new chat session: {session_obj.id} (System prompt length: {len(req.system_prompt)})")
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

    logger.info(f"[API] Received message for session {session_id}: '{req.content[:60]}...'")

    # 1. Save user message to database immediately
    user_msg = await crud.create_message(
        db=db,
        session_id=session_id,
        role=MessageRole.USER,
        content=req.content,
    )

    # 2. Dispatch event processor asynchronously in non-blocking background task
    logger.info(f"[API] Dispatched non-blocking background event processor task for session {session_id}")
    background_tasks.add_task(run_async_event_processor, session_id)

    # 3. Immediately return response without waiting for LLM completion
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


async def trigger_re_ping(session_id: str):
    async with async_session_factory() as db:
        try:
            logger.info(f"[API] Executing in-memory re-ping event processor for session {session_id}...")
            await process_event(db=db, session_id=session_id, trigger_type="scheduled_action")
        except Exception as e:
            logger.error(f"[API] Error executing re-ping event processor for session {session_id}: {e}")
