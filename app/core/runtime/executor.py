from __future__ import annotations

import asyncio
import threading
from collections.abc import Coroutine
from typing import Any, TypeVar

T = TypeVar("T")


class AsyncTaskExecutor:
    """Async task execution foundation with lifecycle management."""

    def __init__(self, max_workers: int = 4) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        self._max_workers = max_workers
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._tasks: set[asyncio.Task[Any]] = set()

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
        )
        self._thread.start()

    def _run_loop(self) -> None:
        if self._loop is None:
            return
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def stop(self) -> None:
        self._running = False
        if self._loop is not None and self._loop.is_running():
            for task in self._tasks:
                task.cancel()
            self._loop.call_soon_threadsafe(self._loop.stop)

    def submit(
        self,
        coro: Coroutine[Any, Any, T],
        name: str | None = None,
    ) -> asyncio.Future[T]:
        if self._loop is None or not self._loop.is_running():
            raise RuntimeError("Executor not running")
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future

    def submit_and_forget(self, coro: Coroutine[Any, Any, Any]) -> None:
        if self._loop is None:
            raise RuntimeError("Executor not running")

        def _done_cb(task: asyncio.Task[Any]) -> None:
            self._tasks.discard(task)

        async def _wrapped() -> None:
            try:
                await coro
            except Exception:
                pass

        task = self._loop.create_task(_wrapped())
        task.add_done_callback(_done_cb)
        self._tasks.add(task)

    def call_later(
        self, delay: float, coro: Coroutine[Any, Any, Any]
    ) -> asyncio.Task[Any]:
        if self._loop is None:
            raise RuntimeError("Executor not running")

        async def _delayed() -> None:
            await asyncio.sleep(delay)
            await coro

        task = self._loop.create_task(_delayed())
        self._tasks.add(task)
        return task

    @property
    def pending_count(self) -> int:
        return len(self._tasks)

    def state(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "max_workers": self._max_workers,
            "pending_tasks": len(self._tasks),
        }
