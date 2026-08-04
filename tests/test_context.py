from datetime import datetime, timedelta, timezone
from app.engine.context import build_llm_messages, format_time_elapsed
from app.models import MessageRole
from app.models.message import MessageModel


def test_format_time_elapsed():
    assert "30 seconds" in format_time_elapsed(30)
    assert "5 minutes" in format_time_elapsed(300)
    assert "1 minute" in format_time_elapsed(60)
    assert "2 hours" in format_time_elapsed(7200)
    assert "1 day" in format_time_elapsed(86400)


def test_build_llm_messages_time_injection():
    now = datetime(2026, 8, 3, 20, 0, 0, tzinfo=timezone.utc)
    past_msg_time = now - timedelta(hours=4)

    msg = MessageModel(
        id="msg-1",
        session_id="session-1",
        role=MessageRole.USER,
        content="Hello!",
        timestamp=past_msg_time,
    )

    payload = build_llm_messages(
        system_prompt="Base system prompt",
        system_instruction="Response Guidelines",
        messages=[msg],
        current_time=now,
    )

    assert len(payload) == 2
    assert payload[0]["role"] == "system"
    assert "# BASE INSTRUCTIONS\nBase system prompt" in payload[0]["content"]
    assert "Current Time: 2026-08-03 08:00 PM UTC" in payload[0]["content"]
    assert "The user sent their message 4 hours ago." in payload[0]["content"]
    assert "Response Guidelines" in payload[0]["content"]
    assert "[TRIGGER: USER_INPUT]" not in payload[0]["content"]  # It uses Trigger: USER_INPUT format now
    assert "Trigger: USER_INPUT" in payload[0]["content"]
    assert payload[1] == {"role": "user", "content": "Hello!"}


def test_build_llm_messages_chronological_ordering():
    now = datetime(2026, 8, 3, 20, 10, 0, tzinfo=timezone.utc)
    t1 = now - timedelta(minutes=5)
    t2 = now - timedelta(minutes=3)
    t3 = now - timedelta(minutes=1)

    m1 = MessageModel(id="1", session_id="s1", role=MessageRole.USER, content="Msg 1 (First)", timestamp=t1)
    m2 = MessageModel(id="2", session_id="s1", role=MessageRole.ASSISTANT, content="Msg 2 (Second)", timestamp=t2)
    m3 = MessageModel(id="3", session_id="s1", role=MessageRole.USER, content="Msg 3 (Third)", timestamp=t3)

    payload = build_llm_messages(
        system_prompt="Test System",
        system_instruction="Format Guidelines",
        messages=[m1, m2, m3],
        current_time=now,
    )

    assert len(payload) == 4
    assert payload[0]["role"] == "system"
    assert "# BASE INSTRUCTIONS\nTest System" in payload[0]["content"]
    assert "Format Guidelines" in payload[0]["content"]
    assert payload[1] == {"role": "user", "content": "Msg 1 (First)"}
    assert payload[2] == {"role": "assistant", "content": "Msg 2 (Second)"}
    assert payload[3] == {"role": "user", "content": "Msg 3 (Third)"}


def test_build_llm_messages_trigger_notices():
    now = datetime(2026, 8, 3, 20, 10, 0, tzinfo=timezone.utc)
    m1 = MessageModel(id="1", session_id="s1", role=MessageRole.USER, content="Msg 1", timestamp=now - timedelta(minutes=1))

    # Test user_input trigger notice
    payload_user = build_llm_messages(
        system_prompt="Test System",
        system_instruction="Guidelines",
        messages=[m1],
        current_time=now,
        trigger_type="user_input"
    )
    assert len(payload_user) == 2
    assert "Trigger: USER_INPUT" in payload_user[0]["content"]
    assert "Respond ONLY to the user's latest input" in payload_user[0]["content"]
    assert payload_user[1] == {"role": "user", "content": "Msg 1"}

    # Test scheduled_action trigger notice
    payload_scheduled = build_llm_messages(
        system_prompt="Test System",
        system_instruction="Guidelines",
        messages=[m1],
        current_time=now,
        trigger_type="scheduled_action"
    )
    assert len(payload_scheduled) == 3
    assert "Trigger: AUTONOMOUS_TIMER_WAKEUP" in payload_scheduled[0]["content"]
    assert payload_scheduled[1] == {"role": "user", "content": "Msg 1"}
    assert payload_scheduled[2]["role"] == "system"
    assert "SYSTEM EVENT: 1 minute have elapsed. Your scheduled timer has expired. The user has not sent any new messages since your last action. Respond to this event now." in payload_scheduled[2]["content"]


