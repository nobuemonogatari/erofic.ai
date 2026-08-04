from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field


class SpeakAction(BaseModel):
    type: Literal["speak"] = "speak"
    content: str = Field(..., description="Message content to respond immediately.")


class LLMActionResponse(BaseModel):
    actions: list[SpeakAction] = Field(default_factory=list, description="List of actions chosen by the LLM.")

