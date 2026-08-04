import asyncio
import logging
from typing import Callable, Coroutine

logger = logging.getLogger(__name__)


class TimerManager:
    """Manages active in-memory session timers to trigger 30-second re-pings."""

    def __init__(self):
        self._timers: dict[str, asyncio.TimerHandle] = {}
        self.trigger_fn: Callable[[str], Coroutine[None, None, None]] | None = None

    def register_trigger_fn(self, fn: Callable[[str], Coroutine[None, None, None]]):
        self.trigger_fn = fn
        logger.info("[TIMER] Registered re-ping trigger function.")

    def schedule_re_ping(self, session_id: str, delay: float = 30.0):
        # Cancel any existing timer for this session
        self.cancel_timer(session_id)

        if not self.trigger_fn:
            logger.error(f"[TIMER] Cannot schedule: trigger_fn not registered.")
            return

        loop = asyncio.get_running_loop()

        async def run():
            try:
                await self.trigger_fn(session_id)
            except Exception as e:
                logger.error(f"[TIMER] Error running trigger for session {session_id}: {e}")

        def run_callback():
            asyncio.create_task(run())

        self._timers[session_id] = loop.call_later(delay, run_callback)
        logger.info(f"[TIMER] Scheduled re-ping in {delay}s for session {session_id}")

    def cancel_timer(self, session_id: str):
        if session_id in self._timers:
            self._timers[session_id].cancel()
            del self._timers[session_id]
            logger.info(f"[TIMER] Cancelled pending timer for session {session_id}")


timer_manager = TimerManager()
