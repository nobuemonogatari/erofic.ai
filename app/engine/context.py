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
    max_history: int = 10,
    current_time: datetime | None = None,
    trigger_type: str = "user_input",
    user_pov_name: str | None = None,
    npc_name: str | None = None,
) -> list[dict[str, str]]:

    now = current_time or datetime.now(timezone.utc)
    llm_payload: list[dict[str, str]] = []

    # 1. Sliding window of recent messages
    recent_messages = list(messages)[-max_history:] if len(messages) > max_history else list(messages)

    # 2. Inject user system_prompt as conversational guidelines
    persona_text = ""
    if system_prompt:
        persona_text = f"3. {system_prompt.strip()}"

    # 3. Format dynamic rules template into guidelines block
    unified_system_content = system_instruction.format(persona_guidelines=persona_text).strip()
    llm_payload.append({"role": "system", "content": unified_system_content})

    # 4. Append chat history with character attribution
    for msg in recent_messages:
        role_str = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
        content_text = msg.content

        # Prefix user actions/speech with protagonist character attribution
        if role_str == "user" and user_pov_name and not content_text.startswith("["):
            content_text = f"[{user_pov_name}'s action/speech]: {content_text}"

        # Prefix assistant actions/speech with NPC character attribution
        elif role_str == "assistant" and npc_name and not content_text.startswith("["):
            content_text = f"[{npc_name}'s turn]: {content_text}"

        llm_payload.append({
            "role": role_str,
            "content": content_text,
        })

    return llm_payload


