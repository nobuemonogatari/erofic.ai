import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator


class SessionLockManager:
    """Manages per-session asyncio.Lock instances to ensure serial execution per session."""

    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    @asynccontextmanager
    async def lock(self, session_id: str) -> AsyncGenerator[None, None]:
        async with self._global_lock:
            if session_id not in self._locks:
                self._locks[session_id] = asyncio.Lock()
            session_lock = self._locks[session_id]

        async with session_lock:
            try:
                yield
            finally:
                async with self._global_lock:
                    if not session_lock.locked() and session_id in self._locks:
                        del self._locks[session_id]


session_lock_manager = SessionLockManager()
