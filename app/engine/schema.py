from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field


class SpeakAction(BaseModel):
    type: Literal["speak"] = "speak"
    content: str = Field(..., description="Message content to respond immediately.")


class SetTimerAction(BaseModel):
    type: Literal["set_timer"] = "set_timer"
    delay_seconds: int = Field(
        ...,
        description="Delay in seconds before waking up the engine.",
        ge=10,
        le=60,
    )


ActionItem = Annotated[Union[SpeakAction, SetTimerAction], Field(discriminator="type")]


class LLMActionResponse(BaseModel):
    actions: list[ActionItem] = Field(default_factory=list, description="List of actions chosen by the LLM.")
