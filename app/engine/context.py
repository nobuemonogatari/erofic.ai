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
    messages: Sequence[MessageModel],
    max_history: int = 20,
    current_time: datetime | None = None,
) -> list[dict[str, str]]:
    now = current_time or datetime.now(timezone.utc)
    llm_payload: list[dict[str, str]] = []

    # 1. Base System Prompt
    if system_prompt:
        llm_payload.append({"role": "system", "content": system_prompt})

    # 2. Sliding window of recent messages
    recent_messages = list(messages)[-max_history:] if len(messages) > max_history else list(messages)

    # 3. Calculate time awareness context
    time_str = now.strftime("%Y-%m-%d %I:%M %p UTC")
    time_info = f"System: It is currently {time_str}."

    if recent_messages:
        last_msg = recent_messages[-1]
        last_ts = last_msg.timestamp
        if last_ts.tzinfo is None:
            last_ts = last_ts.replace(tzinfo=timezone.utc)
        
        elapsed_seconds = max(0.0, (now - last_ts).total_seconds())
        elapsed_str = format_time_elapsed(elapsed_seconds)

        if last_msg.role.value == "user":
            time_info += f" The user sent their message {elapsed_str} ago."
        else:
            time_info += f" The user has not replied in {elapsed_str}."

    llm_payload.append({"role": "system", "content": time_info})

    # 4. Append chat history
    for msg in recent_messages:
        llm_payload.append({
            "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
            "content": msg.content,
        })

    return llm_payload
