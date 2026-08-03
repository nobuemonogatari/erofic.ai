from typing import Literal, Annotated, Union
from pydantic import BaseModel, Field


class SpeakAction(BaseModel):
    type: Literal["speak"] = "speak"
    content: str = Field(..., description="Message content to respond immediately.")


class ScheduleAction(BaseModel):
    type: Literal["schedule"] = "schedule"
    content: str = Field(..., description="Message content to schedule for later.")
    delay_seconds: int = Field(..., description="Delay in seconds before executing message action.", ge=1)


ActionItem = Annotated[Union[SpeakAction, ScheduleAction], Field(discriminator="type")]


class LLMActionResponse(BaseModel):
    actions: list[ActionItem] = Field(default_factory=list, description="List of actions chosen by the LLM.")
