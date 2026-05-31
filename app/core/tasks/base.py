from __future__ import annotations

from enum import Enum, auto
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


class TaskState(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    TIMED_OUT = auto()


class TaskPriority(Enum):
    LOW = 10
    NORMAL = 20
    HIGH = 30
    CRITICAL = 40


TaskFunc = Callable[..., Awaitable[T]]
SyncTaskFunc = Callable[..., T]
