import asyncio
from datetime import datetime, timezone
import logging
from typing import Callable, AsyncContextManager
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import crud
from app.engine.processor import process_event
from app.models import TaskStatus

logger = logging.getLogger(__name__)


class TaskSchedulerWorker:
    def __init__(
        self,
        session_factory: Callable[[], AsyncContextManager[AsyncSession]],
        poll_interval_seconds: float = 1.0,
    ):
        self.session_factory = session_factory
        self.poll_interval = poll_interval_seconds
        self._task: asyncio.Task | None = None
        self._running = False

    async def run_once(self) -> int:
        processed_count = 0
        now = datetime.now(timezone.utc)

        async with self.session_factory() as db:
            due_tasks = await crud.get_pending_tasks_due(db, now=now)
            if due_tasks:
                logger.info(f"[SCHEDULER] Found {len(due_tasks)} pending task(s) due at or before {now.strftime('%H:%M:%S UTC')}")

            for task in due_tasks:
                # IDEMPOTENCY: Mark completed BEFORE executing trigger
                logger.info(f"[SCHEDULER] Marking task {task.id} (Session {task.session_id}) as COMPLETED")
                await crud.mark_task_status(db, task.id, TaskStatus.COMPLETED)
                try:
                    logger.info(f"[SCHEDULER] Triggering process_event for task {task.id} (Session {task.session_id})...")
                    await process_event(db, task.session_id, trigger_type="scheduled_action")
                    processed_count += 1
                except Exception as e:
                    logger.error(f"[SCHEDULER] Error executing scheduled task {task.id}: {e}")

        return processed_count

    async def _loop(self) -> None:
        logger.info("Background task scheduler worker loop active (polling every 1.0s).")
        while self._running:
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"[SCHEDULER] Exception in worker loop: {e}")
            await asyncio.sleep(self.poll_interval)
        logger.info("Background task scheduler worker loop terminated.")

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            self._task = None
