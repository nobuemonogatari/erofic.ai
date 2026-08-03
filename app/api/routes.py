from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    MessageCreateRequest,
    MessageResponse,
    SessionCreateRequest,
    SessionResponse,
)
from app.db import crud
from app.db.session import get_async_session
from app.engine.processor import process_event
from app.models import MessageRole

router = APIRouter()


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session_endpoint(
    req: SessionCreateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    session_obj = await crud.create_session(db, system_prompt=req.system_prompt)
    return session_obj


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions_endpoint(
    db: AsyncSession = Depends(get_async_session),
):
    sessions = await crud.get_all_sessions(db)
    return sessions


@router.post("/sessions/{session_id}/message", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message_endpoint(
    session_id: str,
    req: MessageCreateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    session_obj = await crud.get_session(db, session_id)
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    # 1. Save user message to database
    user_msg = await crud.create_message(
        db=db,
        session_id=session_id,
        role=MessageRole.USER,
        content=req.content,
    )

    # 2. Trigger Event Processor (Executes LLM logic & handles actions)
    await process_event(db=db, session_id=session_id, trigger_type="user_input")

    return user_msg


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages_endpoint(
    session_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    session_obj = await crud.get_session(db, session_id)
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    messages = await crud.get_messages_for_session(db, session_id)
    return messages
