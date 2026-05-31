from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from dataclasses import dataclass, field
from typing import Any, TypeVar

from app.core.tasks.base import TaskPriority, TaskState

T = TypeVar("T")


@dataclass(order=True)
class _PrioritizedEntry:
    priority: int
    seq: int = field(compare=False)
    task_id: str = field(compare=False)
    coro: Coroutine[Any, Any, Any] = field(compare=False)


class BackgroundJobQueue:
    """Internal background job queue with priority scheduling."""

    def __init__(self, max_size: int = 1000) -> None:
        if max_size < 1:
            raise ValueError("max_size must be >= 1")
        self._max_size = max_size
        self._queue: asyncio.PriorityQueue[_PrioritizedEntry] = (
            asyncio.PriorityQueue(maxsize=max_size)
        )
        self._results: dict[str, Any] = {}
        self._errors: dict[str, Exception] = {}
        self._states: dict[str, TaskState] = {}
        self._lock = asyncio.Lock()
        self._seq = 0

    @property
    def max_size(self) -> int:
        return self._max_size

    @property
    def qsize(self) -> int:
        return self._queue.qsize()

    async def enqueue(
        self,
        task_id: str,
        coro: Coroutine[Any, Any, T],
        priority: TaskPriority = TaskPriority.NORMAL,
    ) -> str:
        if len(self._states) >= self._max_size:
            raise RuntimeError(f"Queue full ({self._max_size} max)")
        self._seq += 1
        entry = _PrioritizedEntry(
            priority=-priority.value,
            seq=self._seq,
            task_id=task_id,
            coro=coro,
        )
        async with self._lock:
            self._states[task_id] = TaskState.PENDING
        await self._queue.put(entry)
        return task_id

    async def process_next(
        self, timeout: float | None = None
    ) -> str | None:
        try:
            entry = await asyncio.wait_for(
                self._queue.get(), timeout=timeout
            )
        except asyncio.TimeoutError:
            return None
        async with self._lock:
            self._states[entry.task_id] = TaskState.RUNNING
        try:
            result = await entry.coro
            async with self._lock:
                self._results[entry.task_id] = result
                self._states[entry.task_id] = TaskState.COMPLETED
        except asyncio.CancelledError:
            async with self._lock:
                self._states[entry.task_id] = TaskState.CANCELLED
        except Exception as exc:
            async with self._lock:
                self._errors[entry.task_id] = exc
                self._states[entry.task_id] = TaskState.FAILED
        finally:
            self._queue.task_done()
        return entry.task_id

    async def process_all(self, max_batch: int = 0) -> list[str]:
        completed: list[str] = []
        limit = max_batch if max_batch > 0 else self._queue.qsize()
        for _ in range(limit):
            tid = await self.process_next()
            if tid is None:
                break
            completed.append(tid)
        return completed

    def get_result(self, task_id: str) -> Any:
        return self._results.get(task_id)

    def get_error(self, task_id: str) -> Exception | None:
        return self._errors.get(task_id)

    def get_state(self, task_id: str) -> TaskState | None:
        return self._states.get(task_id)

    async def cancel(self, task_id: str) -> bool:
        async with self._lock:
            state = self._states.get(task_id)
            if state is None or state in (
                TaskState.COMPLETED,
                TaskState.FAILED,
                TaskState.CANCELLED,
            ):
                return False
            self._states[task_id] = TaskState.CANCELLED
            return True

    async def clear_completed(self) -> int:
        cleared = 0
        async with self._lock:
            for tid in list(self._states.keys()):
                state = self._states[tid]
                if state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED):
                    del self._states[tid]
                    self._results.pop(tid, None)
                    self._errors.pop(tid, None)
                    cleared += 1
        return cleared

    async def join(self) -> None:
        await self._queue.join()

    def state_summary(self) -> dict[str, int]:
        summary: dict[str, int] = {}
        for state in TaskState:
            summary[state.name.lower()] = 0
        for s in self._states.values():
            summary[s.name.lower()] += 1
        return summary
