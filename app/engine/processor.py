from datetime import datetime, timedelta, timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.engine.context import build_llm_messages
from app.engine.guardrails import check_recursion_limit
from app.engine.llm import LLMClient, LLMGenerationError, SYSTEM_JSON_INSTRUCTION
from app.engine.lock import session_lock_manager
from app.models import MessageRole
from app.scheduler.manager import timer_manager

logger = logging.getLogger(__name__)

DEFAULT_WAKEUP_TIMER_SECONDS = 30
ERROR_RETRY_TIMER_SECONDS = 10


async def process_event(
    db: AsyncSession,
    session_id: str,
    trigger_type: str = "user_input",
    llm_client: LLMClient | None = None,
) -> dict[str, str | int]:
    async with session_lock_manager.lock(session_id):
        logger.info(f"[ENGINE] Starting event cycle for session {session_id} (trigger: {trigger_type})")

        # Cancel any pending in-memory timers for this session immediately
        timer_manager.cancel_timer(session_id)

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

        # 3. Build context payload with system time awareness
        now = datetime.now(timezone.utc)
        llm_payload = build_llm_messages(
            system_prompt=session_obj.system_prompt,
            system_instruction=SYSTEM_JSON_INSTRUCTION,
            messages=messages,
            current_time=now,
            trigger_type=trigger_type,
        )
        logger.debug(f"[ENGINE] Prepared LLM payload with {len(llm_payload)} items (including time awareness)")

        # 4. Call LLM Client
        client = llm_client or LLMClient()
        logger.info(f"[ENGINE] Invoking LLM (model: {client.model})...")
        try:
            llm_response = await client.generate_actions(llm_payload)
        except (LLMGenerationError, Exception) as e:
            logger.error(f"[ENGINE] LLM call failed for session {session_id}: {e}")
            # Schedule fast 10s error retry in-memory timer
            timer_manager.schedule_re_ping(session_id, delay=ERROR_RETRY_TIMER_SECONDS)
            logger.warning(
                f"[ERROR_RETRY] Scheduled {ERROR_RETRY_TIMER_SECONDS}s error retry in-memory timer for session {session_id} due to LLM error"
            )
            return {
                "status": "error",
                "reason": f"LLM generation failed: {e}",
                "timers_set": 1,
            }

        logger.info(f"[ENGINE] LLM returned {len(llm_response)} sequential message(s)")

        # 5. Execute LLM actions
        spoken_count = 0
        for i, content in enumerate(llm_response):
            msg_time = now + timedelta(milliseconds=i * 50)
            await crud.create_message(
                db=db,
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=content,
                timestamp=msg_time,
            )
            spoken_count += 1
            logger.info(f"[ACTION:SPEAK] Saved assistant message to session {session_id}: '{content[:60]}...'")

        # 6. Always schedule default in-memory wake-up / re-ping timer (30s)
        timer_manager.schedule_re_ping(session_id, delay=DEFAULT_WAKEUP_TIMER_SECONDS)
        logger.info(f"[DEFAULT_TIMER] Scheduled default {DEFAULT_WAKEUP_TIMER_SECONDS}s re-ping in-memory timer for session {session_id}")

        logger.info(f"[ENGINE] Completed event cycle for session {session_id}: spoken={spoken_count}, timers_set=1")

        return {
            "status": "success",
            "spoken": spoken_count,
            "timers_set": 1,
        }


