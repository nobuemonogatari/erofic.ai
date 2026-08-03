from datetime import datetime, timedelta, timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.engine.context import build_llm_messages
from app.engine.guardrails import check_recursion_limit
from app.engine.llm import LLMClient
from app.models import MessageRole

logger = logging.getLogger(__name__)


async def process_event(
    db: AsyncSession,
    session_id: str,
    trigger_type: str = "user_input",
    llm_client: LLMClient | None = None,
) -> dict[str, str | int]:
    # 1. Fetch Session and Message history from SQLite
    session_obj = await crud.get_session(db, session_id)
    if not session_obj:
        logger.error(f"Session {session_id} not found.")
        return {"status": "error", "reason": "Session not found"}

    messages = await crud.get_messages_for_session(db, session_id)

    # 2. Check recursion limit guardrail
    if not check_recursion_limit(messages):
        logger.warning(
            f"Recursion limit reached for session {session_id}. Aborting autonomous actions."
        )
        return {"status": "aborted", "reason": "Recursion limit reached"}

    # 3. Auto-cancel any existing pending timers for this session
    cancelled_timers = await crud.cancel_pending_tasks_for_session(db, session_id)
    if cancelled_timers > 0:
        logger.info(f"Cancelled {cancelled_timers} pending timer(s) for session {session_id}.")

    # 4. Build context payload with system time awareness
    now = datetime.now(timezone.utc)
    llm_payload = build_llm_messages(
        system_prompt=session_obj.system_prompt,
        messages=messages,
        current_time=now,
    )

    # 5. Call LLM Client
    client = llm_client or LLMClient()
    llm_response = await client.generate_actions(llm_payload)

    # 6. Execute LLM actions
    spoken_count = 0
    timers_set_count = 0

    for action in llm_response.actions:
        action_type = action.type
        if action_type == "speak":
            await crud.create_message(
                db=db,
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=action.content,
                timestamp=now,
            )
            spoken_count += 1
        elif action_type == "set_timer":
            execute_at = now + timedelta(seconds=action.delay_seconds)
            await crud.create_scheduled_task(
                db=db,
                session_id=session_id,
                execute_at=execute_at,
            )
            timers_set_count += 1

    return {
        "status": "success",
        "spoken": spoken_count,
        "timers_set": timers_set_count,
    }
