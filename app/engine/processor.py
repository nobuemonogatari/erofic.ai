from datetime import datetime, timedelta, timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.engine.context import build_llm_messages
from app.engine.guardrails import check_recursion_limit
from app.engine.llm import LLMClient
from app.models import MessageRole

logger = logging.getLogger(__name__)

DEFAULT_WAKEUP_TIMER_SECONDS = 60


async def process_event(
    db: AsyncSession,
    session_id: str,
    trigger_type: str = "user_input",
    llm_client: LLMClient | None = None,
) -> dict[str, str | int]:
    logger.info(f"[ENGINE] Starting event cycle for session {session_id} (trigger: {trigger_type})")

    # 1. Fetch Session and Message history from SQLite
    session_obj = await crud.get_session(db, session_id)
    if not session_obj:
        logger.error(f"[ENGINE] Session {session_id} not found in database. Aborting event.")
        return {"status": "error", "reason": "Session not found"}

    messages = await crud.get_messages_for_session(db, session_id)
    logger.info(f"[ENGINE] Loaded history for session {session_id}: {len(messages)} message(s)")

    # 2. Check recursion limit guardrail
    if not check_recursion_limit(messages):
        logger.warning(
            f"[GUARDRAIL] Recursion limit reached for session {session_id} (>= 3 consecutive assistant messages). Aborting."
        )
        return {"status": "aborted", "reason": "Recursion limit reached"}

    # 3. Auto-cancel any existing pending timers for this session
    cancelled_timers = await crud.cancel_pending_tasks_for_session(db, session_id)
    if cancelled_timers > 0:
        logger.info(f"[ENGINE] Auto-cancelled {cancelled_timers} pending timer(s) for session {session_id}.")

    # 4. Build context payload with system time awareness
    now = datetime.now(timezone.utc)
    llm_payload = build_llm_messages(
        system_prompt=session_obj.system_prompt,
        messages=messages,
        current_time=now,
    )
    logger.debug(f"[ENGINE] Prepared LLM payload with {len(llm_payload)} items (including time awareness)")

    # 5. Call LLM Client
    client = llm_client or LLMClient()
    logger.info(f"[ENGINE] Invoking LLM (model: {client.model})...")
    llm_response = await client.generate_actions(llm_payload)
    logger.info(f"[ENGINE] LLM returned {len(llm_response.actions)} action(s)")

    # 6. Execute LLM actions
    spoken_count = 0
    timers_set_count = 0

    for i, action in enumerate(llm_response.actions):
        action_type = action.type
        if action_type == "speak":
            msg_time = now + timedelta(milliseconds=i * 50)
            await crud.create_message(
                db=db,
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=action.content,
                timestamp=msg_time,
            )
            spoken_count += 1
            logger.info(f"[ACTION:SPEAK] Saved assistant message to session {session_id}: '{action.content[:60]}...'")

        elif action_type == "set_timer":
            # Strict Invariant: At most 1 pending timer per session
            await crud.cancel_pending_tasks_for_session(db, session_id)
            execute_at = now + timedelta(seconds=action.delay_seconds)
            task = await crud.create_scheduled_task(
                db=db,
                session_id=session_id,
                execute_at=execute_at,
            )
            timers_set_count = 1
            logger.info(f"[ACTION:SET_TIMER] LLM requested wake-up timer for session {session_id} in {action.delay_seconds}s (execute_at: {execute_at.strftime('%H:%M:%S UTC')}, Task ID: {task.id})")

    # 7. Default wake-up timer fallback if no timer was explicitly set by LLM
    if timers_set_count == 0:
        await crud.cancel_pending_tasks_for_session(db, session_id)
        execute_at = now + timedelta(seconds=DEFAULT_WAKEUP_TIMER_SECONDS)
        task = await crud.create_scheduled_task(
            db=db,
            session_id=session_id,
            execute_at=execute_at,
        )
        timers_set_count = 1
        logger.info(f"[DEFAULT_TIMER] Scheduled default {DEFAULT_WAKEUP_TIMER_SECONDS}s wake-up timer for session {session_id} (execute_at: {execute_at.strftime('%H:%M:%S UTC')}, Task ID: {task.id})")

    logger.info(f"[ENGINE] Completed event cycle for session {session_id}: spoken={spoken_count}, timers_set={timers_set_count}")

    return {
        "status": "success",
        "spoken": spoken_count,
        "timers_set": timers_set_count,
    }
