from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from threading import Thread
from typing import Any, Callable


class TaskPriority(Enum):
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()


class TaskState(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class TaskHandle:
    task_id: str
    state: TaskState = TaskState.PENDING
    result: Any = None
    error: Exception | None = None

    @property
    def done(self) -> bool:
        return self.state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED)

    @property
    def failed(self) -> bool:
        return self.state == TaskState.FAILED


@dataclass
class AsyncTask:
    name: str
    fn: Callable[[], Any]
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_ms: int = 30_000
    retry_on_failure: bool = False
    max_retries: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AsyncBridge:
    def __init__(self, max_workers: int = 4):
        self._max_workers = max_workers
        self._handles: dict[str, TaskHandle] = {}
        self._shutdown = False

    def submit(self, task: AsyncTask) -> TaskHandle:
        if self._shutdown:
            raise RuntimeError("AsyncBridge is shut down")
        handle = TaskHandle(task_id=task.name)
        self._handles[task.name] = handle
        thread = Thread(target=self._run_task, args=(task, handle), daemon=True)
        thread.start()
        return handle

    def _run_task(self, task: AsyncTask, handle: TaskHandle) -> None:
        try:
            handle.state = TaskState.RUNNING
            result = task.fn()
            handle.state = TaskState.COMPLETED
            handle.result = result
        except Exception as e:
            handle.state = TaskState.FAILED
            handle.error = e

    def cancel(self, task_id: str) -> bool:
        handle = self._handles.get(task_id)
        if handle and not handle.done:
            handle.state = TaskState.CANCELLED
            return True
        return False

    def status(self, task_id: str) -> TaskHandle | None:
        return self._handles.get(task_id)

    def shutdown(self) -> None:
        self._shutdown = True
        for handle in self._handles.values():
            if not handle.done:
                handle.state = TaskState.CANCELLED

    @property
    def pending_count(self) -> int:
        return sum(1 for h in self._handles.values() if h.state == TaskState.PENDING)

    @property
    def running_count(self) -> int:
        return sum(1 for h in self._handles.values() if h.state == TaskState.RUNNING)
