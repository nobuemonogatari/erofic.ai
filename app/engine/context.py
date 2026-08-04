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

    # 1. Sliding window of recent messages
    recent_messages = list(messages)[-max_history:] if len(messages) > max_history else list(messages)

    # 2. Time context
    time_str = now.strftime("%Y-%m-%d %I:%M %p UTC")
    time_info = f"- Current Time: {time_str}"
    
    elapsed_str = ""
    if recent_messages:
        last_msg = recent_messages[-1]
        last_ts = last_msg.timestamp
        if last_ts.tzinfo is None:
            last_ts = last_ts.replace(tzinfo=timezone.utc)
        
        elapsed_seconds = max(0.0, (now - last_ts).total_seconds())
        elapsed_val = format_time_elapsed(elapsed_seconds)

        if last_msg.role.value == "user":
            elapsed_str = f"- Time Elapsed: The user sent their message {elapsed_val} ago."
        else:
            elapsed_str = f"- Time Elapsed: The user has not replied in {elapsed_val}."

    time_context = f"{time_info}\n{elapsed_str}".strip()

    # 3. Trigger / Event notice context
    if trigger_type == "scheduled_action":
        trigger_notice = (
            "- Trigger: AUTONOMOUS_TIMER_WAKEUP\n"
            "- Notice: This is an autonomous wake-up event because your scheduled timer has expired.\n"
            "  The user has NOT sent a new message since your last reply.\n"
            "  All previous messages in the history have already been sent to the user.\n"
            "  DO NOT repeat, re-answer, or summarize any previous assistant messages in the chat history.\n"
            "  Either send a natural follow-up double-text if appropriate, or set a timer to keep waiting."
        )
    else:
        trigger_notice = (
            "- Trigger: USER_INPUT\n"
            "- Notice: The user has sent a new message. Respond ONLY to the user's latest input.\n"
            "  Review the chat history for context, but do not repeat or re-state previous assistant replies."
        )

    # 4. Construct unified system block
    system_parts = []
    if system_prompt:
        system_parts.append(f"# BASE INSTRUCTIONS\n{system_prompt}")
    
    system_parts.append(f"# TIME CONTEXT\n{time_context}")
    system_parts.append(f"# RESPONSE RULES & FORMAT GUIDELINES\n{system_instruction}")
    system_parts.append(f"# EVENT CONTEXT\n{trigger_notice}")

    unified_system_content = "\n\n".join(system_parts)
    llm_payload.append({"role": "system", "content": unified_system_content})

    # 5. Append chat history
    for msg in recent_messages:
        llm_payload.append({
            "role": msg.role.value if hasattr(msg.role, "value") else str(msg.role),
            "content": msg.content,
        })

    # 6. Append trailing system notice if it is a scheduled_action
    if trigger_type == "scheduled_action":
        elapsed_val = "10 seconds"
        if recent_messages:
            last_msg = recent_messages[-1]
            last_ts = last_msg.timestamp
            if last_ts.tzinfo is None:
                last_ts = last_ts.replace(tzinfo=timezone.utc)
            elapsed_seconds = max(0.0, (now - last_ts).total_seconds())
            elapsed_val = format_time_elapsed(elapsed_seconds)

        trailing_event_notice = (
            f"SYSTEM EVENT: {elapsed_val} have elapsed. Your scheduled timer has expired. "
            "The user has not sent any new messages since your last action. Respond to this event now."
        )
        llm_payload.append({"role": "system", "content": trailing_event_notice})

    return llm_payload


