import asyncio
import gc
import pytest

from app.engine.lock import SessionLockManager


@pytest.mark.asyncio
async def test_session_lock_manager_serialization():
    manager = SessionLockManager()
    execution_order = []

    async def worker(task_id: int, delay: float):
        async with manager.lock("session_1"):
            execution_order.append(f"start_{task_id}")
            await asyncio.sleep(delay)
            execution_order.append(f"end_{task_id}")

    # Run worker 1 and worker 2 concurrently for session_1
    await asyncio.gather(
        worker(1, 0.05),
        worker(2, 0.01),
    )

    # Worker 1 should completely finish before Worker 2 starts
    assert execution_order == ["start_1", "end_1", "start_2", "end_2"]


@pytest.mark.asyncio
async def test_session_lock_manager_auto_cleanup():
    manager = SessionLockManager()
    session_id = "temp_session"

    async with manager.lock(session_id):
        assert session_id in manager._locks

    # Trigger garbage collection to clean up weak references
    gc.collect()

    # The lock should now be automatically removed from _locks
    assert session_id not in manager._locks
