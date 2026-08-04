from datetime import datetime, timedelta, timezone
from app.models.message import MessageModel
from app.models import MessageRole
from app.engine.context import build_llm_messages


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
        system_instruction="Response Guidelines\n{persona_guidelines}",
        messages=[msg],
        current_time=now,
    )

    # 1 system instruction + 1 user message = 2 messages total
    assert len(payload) == 2
    assert payload[0]["role"] == "system"
    assert "Base system prompt" in payload[0]["content"]
    assert "Response Guidelines\n3. Base system prompt" in payload[0]["content"]
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
        system_instruction="Format Guidelines\n{persona_guidelines}",
        messages=[m1, m2, m3],
        current_time=now,
    )

    # 1 system instruction + 3 chat messages = 4 messages total
    assert len(payload) == 4
    assert payload[0]["role"] == "system"
    assert "Test System" in payload[0]["content"]
    assert "Format Guidelines\n3. Test System" in payload[0]["content"]
    assert payload[1] == {"role": "user", "content": "Msg 1 (First)"}
    assert payload[2] == {"role": "assistant", "content": "Msg 2 (Second)"}
    assert payload[3] == {"role": "user", "content": "Msg 3 (Third)"}


def test_build_llm_messages_trigger_notices():
    now = datetime(2026, 8, 3, 20, 10, 0, tzinfo=timezone.utc)
    m1 = MessageModel(id="1", session_id="s1", role=MessageRole.USER, content="Msg 1", timestamp=now - timedelta(minutes=1))

    # Test user_input trigger notice formatting
    payload_user = build_llm_messages(
        system_prompt="Test System",
        system_instruction="Guidelines\n{persona_guidelines}",
        messages=[m1],
        current_time=now,
        trigger_type="user_input"
    )
    assert len(payload_user) == 2
    assert payload_user[0]["role"] == "system"
    assert "Test System" in payload_user[0]["content"]
    assert payload_user[1] == {"role": "user", "content": "Msg 1"}

    # Test scheduled_action trigger notice formatting
    payload_scheduled = build_llm_messages(
        system_prompt="Test System",
        system_instruction="Guidelines\n{persona_guidelines}",
        messages=[m1],
        current_time=now,
        trigger_type="scheduled_action"
    )
    assert len(payload_scheduled) == 2
    assert payload_scheduled[0]["role"] == "system"
    assert "Test System" in payload_scheduled[0]["content"]
    assert payload_scheduled[1] == {"role": "user", "content": "Msg 1"}
