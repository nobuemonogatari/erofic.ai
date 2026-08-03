from typing import Sequence
from app.models import MessageRole
from app.models.message import MessageModel

MAX_CONSECUTIVE_ASSISTANT_MESSAGES = 3


def check_recursion_limit(messages: Sequence[MessageModel]) -> bool:
    """
    Returns True if the assistant can respond/schedule.
    Returns False if recursion limit is reached (assistant has sent >= 3 consecutive messages without user input).
    """
    consecutive_assistant = 0
    for msg in reversed(messages):
        role_val = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
        if role_val == MessageRole.ASSISTANT.value:
            consecutive_assistant += 1
        elif role_val == MessageRole.USER.value:
            break

    return consecutive_assistant < MAX_CONSECUTIVE_ASSISTANT_MESSAGES
