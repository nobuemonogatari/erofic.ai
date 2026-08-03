from typing import Literal
from pydantic import BaseModel, Field


class SpeakAction(BaseModel):
    type: Literal["speak"] = "speak"
    content: str = Field(..., description="Message content to respond immediately.")


ActionItem = SpeakAction


class LLMActionResponse(BaseModel):
    actions: list[ActionItem] = Field(default_factory=list, description="List of actions chosen by the LLM.")
