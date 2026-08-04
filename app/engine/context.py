from datetime import datetime, timezone
from typing import Sequence

from app.models.message import MessageModel


def format_time_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''}"
    else:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days != 1 else ''}"


def build_llm_messages(
    system_prompt: str,
    system_instruction: str,
    messages: Sequence[MessageModel],
    max_history: int = 20,
    current_time: datetime | None = None,
    trigger_type: str = "user_input",
) -> list[dict[str, str]]:
    now = current_time or datetime.now(timezone.utc)
    llm_payload: list[dict[str, str]] = []

    # 1. Unified static system prompt at index 0
    system_parts = []
    if system_prompt:
        system_parts.append(f"# Persona & Instructions\n{system_prompt}")
    system_parts.append(f"# Response Rules & Guidelines\n{system_instruction}")
    unified_system_content = "\n\n".join(system_parts)
    llm_payload.append({"role": "system", "content": unified_system_content})

    # 2. Sliding window of recent messages
    recent_messages = list(messages)[-max_history:] if len(messages) > max_history else list(messages)

    # 3. Append chat history
    for msg in recent_messages:
        llm_payload.append({
            "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
            "content": msg.content,
        })

    # 4. Calculate relative elapsed time
    elapsed_val = "30 seconds"
    if recent_messages:
        last_msg = recent_messages[-1]
        last_ts = last_msg.timestamp
        if last_ts.tzinfo is None:
            last_ts = last_ts.replace(tzinfo=timezone.utc)
        elapsed_seconds = max(0.0, (now - last_ts).total_seconds())
        elapsed_val = format_time_elapsed(elapsed_seconds)

    # 5. Append consolidated Event Context at the very end
    if trigger_type == "scheduled_action":
        end_event_notice = (
            f"SYSTEM EVENT [AUTONOMOUS_RE_PING]: {elapsed_val} have elapsed since your last action. "
            "The user has not replied. Decide if you want to follow up or remain silent (return an empty actions list)."
        )
    else:
        end_event_notice = (
            f"SYSTEM EVENT [USER_INPUT]: The user sent a new message {elapsed_val} ago. "
            "Respond ONLY to the user's latest input."
        )

    llm_payload.append({"role": "system", "content": end_event_notice})

    return llm_payload
