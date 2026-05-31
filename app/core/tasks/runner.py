from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class BoundedTaskRunner(Generic[T]):
    """Runs tasks with bounded concurrency, timeout, and cancellation."""

    def __init__(
        self,
        max_concurrency: int = 4,
        default_timeout: float = 30.0,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be >= 1")
        if default_timeout <= 0:
            raise ValueError("default_timeout must be > 0")
        self._max_concurrency = max_concurrency
        self._default_timeout = default_timeout
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._active: dict[str, asyncio.Task[Any]] = {}
        self._lock = asyncio.Lock()
        self._shutdown = False

    @property
    def max_concurrency(self) -> int:
        return self._max_concurrency

    @property
    def active_count(self) -> int:
        return len(self._active)

    @property
    def is_shutdown(self) -> bool:
        return self._shutdown

    async def run(
        self,
        coro: Coroutine[Any, Any, T],
        task_id: str | None = None,
        timeout: float | None = None,
    ) -> T:
        if self._shutdown:
            raise RuntimeError("Runner is shut down")
        _timeout = timeout if timeout is not None else self._default_timeout
        async with self._semaphore:
            task = asyncio.create_task(self._execute(coro, _timeout))
            tid = task_id or f"task_{id(task)}"
            async with self._lock:
                self._active[tid] = task
            try:
                return await task
            finally:
                async with self._lock:
                    self._active.pop(tid, None)

    async def _execute(
        self, coro: Coroutine[Any, Any, T], timeout: float
    ) -> T:
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Task timed out after {timeout}s"
            )
        except asyncio.CancelledError:
            raise RuntimeError("Task cancelled")

    async def cancel(self, task_id: str) -> bool:
        async with self._lock:
            task = self._active.get(task_id)
            if task is None or task.done():
                return False
            task.cancel()
            return True

    async def cancel_all(self) -> int:
        cancelled = 0
        async with self._lock:
            for tid, task in list(self._active.items()):
                if not task.done():
                    task.cancel()
                    cancelled += 1
        return cancelled

    async def shutdown(self, wait: bool = True) -> None:
        self._shutdown = True
        await self.cancel_all()
        if wait and self._active:
            async with self._lock:
                remaining = list(self._active.values())
            await asyncio.gather(*remaining, return_exceptions=True)

    def state(self) -> dict[str, Any]:
        return {
            "max_concurrency": self._max_concurrency,
            "active_count": self.active_count,
            "shutdown": self._shutdown,
        }
