from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class CommandPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class CommandState(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    DISPATCHING = "dispatching"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    DEAD_LETTER = "dead_letter"


@dataclass
class CommandStatus:
    state: CommandState = CommandState.PENDING
    attempts: int = 0
    max_attempts: int = 3
    last_error: str = ""
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    dispatched_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass
class CommandEntry:
    command_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    command_type: str = ""
    aggregate_id: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    priority: CommandPriority = CommandPriority.NORMAL
    status: CommandStatus = field(default_factory=CommandStatus)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def state(self) -> CommandState:
        return self.status.state

    @property
    def is_expired(self) -> bool:
        if self.status.max_attempts <= 0:
            return False
        return self.status.attempts >= self.status.max_attempts


class CommandLifecycle:
    """Crash-safe command lifecycle with retry and dead-letter support."""

    def __init__(self, max_attempts: int = 3) -> None:
        self._max_attempts = max_attempts

    def prepare(self, command: CommandEntry) -> None:
        command.status.state = CommandState.QUEUED
        command.status.created_at = datetime.now(timezone.utc)

    def mark_dispatched(self, command: CommandEntry) -> None:
        command.status.state = CommandState.DISPATCHING
        command.status.dispatched_at = datetime.now(timezone.utc)

    def mark_completed(self, command: CommandEntry) -> None:
        command.status.state = CommandState.COMPLETED
        command.status.completed_at = datetime.now(timezone.utc)

    def mark_failed(
        self, command: CommandEntry, error: str = ""
    ) -> None:
        command.status.attempts += 1
        command.status.last_error = error
        if command.is_expired:
            command.status.state = CommandState.DEAD_LETTER
        else:
            command.status.state = CommandState.FAILED

    def can_retry(self, command: CommandEntry) -> bool:
        return (
            command.status.state in (CommandState.FAILED,)
            and command.status.attempts < self._max_attempts
        )
