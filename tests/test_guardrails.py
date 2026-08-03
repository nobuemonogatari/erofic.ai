from app.engine.guardrails import check_recursion_limit
from app.models import MessageRole
from app.models.message import MessageModel


def test_check_recursion_limit_pass():
    messages = [
        MessageModel(id="1", session_id="s1", role=MessageRole.USER, content="Hi"),
        MessageModel(id="2", session_id="s1", role=MessageRole.ASSISTANT, content="Hello"),
        MessageModel(id="3", session_id="s1", role=MessageRole.ASSISTANT, content="How are you?"),
    ]
    assert check_recursion_limit(messages) is True


def test_check_recursion_limit_block():
    messages = [
        MessageModel(id="1", session_id="s1", role=MessageRole.USER, content="Hi"),
        MessageModel(id="2", session_id="s1", role=MessageRole.ASSISTANT, content="Msg 1"),
        MessageModel(id="3", session_id="s1", role=MessageRole.ASSISTANT, content="Msg 2"),
        MessageModel(id="4", session_id="s1", role=MessageRole.ASSISTANT, content="Msg 3"),
    ]
    assert check_recursion_limit(messages) is False
