import asyncio
import weakref
from contextlib import asynccontextmanager
from typing import AsyncGenerator


class SessionLockManager:
    """Manages per-session asyncio.Lock instances to ensure serial execution per session."""

    def __init__(self) -> None:
        self._locks: weakref.WeakValueDictionary[str, asyncio.Lock] = weakref.WeakValueDictionary()
        self._global_lock = asyncio.Lock()

    @asynccontextmanager
    async def lock(self, session_id: str) -> AsyncGenerator[None, None]:
        async with self._global_lock:
            session_lock = self._locks.get(session_id)
            if session_lock is None:
                session_lock = asyncio.Lock()
                self._locks[session_id] = session_lock

        async with session_lock:
            yield


session_lock_manager = SessionLockManager()

