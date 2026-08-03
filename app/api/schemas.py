from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models import MessageRole, TaskStatus


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


class TaskResponse(BaseModel):
    id: str
    session_id: str
    execute_at: datetime
    status: TaskStatus

    model_config = ConfigDict(from_attributes=True)
