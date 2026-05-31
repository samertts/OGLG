from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from app.core.queue.commands import (
    CommandEntry,
    CommandLifecycle,
    CommandPriority,
)


class CommandDispatcher:
    """Persistent command dispatcher with bounded execution and retry."""

    def __init__(
        self,
        max_concurrency: int = 4,
        default_timeout: float = 30.0,
        max_attempts: int = 3,
    ) -> None:
        self._max_concurrency = max_concurrency
        self._default_timeout = default_timeout
        self._lifecycle = CommandLifecycle(max_attempts=max_attempts)
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._queue: list[CommandEntry] = []
        self._dead_letter: list[CommandEntry] = []
        self._lock = threading.RLock()
        self._active = 0
        self._total_dispatched = 0
        self._total_failed = 0

    def register_handler(
        self,
        command_type: str,
        handler: Callable[..., Any],
    ) -> None:
        with self._lock:
            self._handlers[command_type] = handler

    def enqueue(self, command: CommandEntry) -> None:
        with self._lock:
            self._lifecycle.prepare(command)
            self._queue.append(command)
            self._queue.sort(
                key=lambda c: c.priority.value, reverse=True
            )

    def enqueue_command(
        self,
        command_type: str,
        aggregate_id: str = "",
        payload: dict[str, Any] | None = None,
        priority: CommandPriority = CommandPriority.NORMAL,
    ) -> CommandEntry:
        cmd = CommandEntry(
            command_type=command_type,
            aggregate_id=aggregate_id,
            payload=payload or {},
            priority=priority,
        )
        self.enqueue(cmd)
        return cmd

    def dispatch_next(
        self, timeout: float | None = None
    ) -> CommandEntry | None:
        _timeout = timeout or self._default_timeout
        command: CommandEntry | None = None
        with self._lock:
            if self._active >= self._max_concurrency:
                return None
            if not self._queue:
                return None
            command = self._queue.pop(0)
            self._active += 1

        if command is None:
            return None

        handler = self._handlers.get(command.command_type)
        if handler is None:
            self._lifecycle.mark_failed(
                command, f"No handler for {command.command_type}"
            )
            self._dead_letter.append(command)
            with self._lock:
                self._active -= 1
                self._total_failed += 1
            return command

        self._lifecycle.mark_dispatched(command)
        result: list[Exception | None] = [None]
        event = threading.Event()

        def _execute() -> None:
            try:
                handler(command)
            except Exception as exc:
                result[0] = exc
            finally:
                event.set()

        thread = threading.Thread(target=_execute, daemon=True)
        thread.start()
        ok = event.wait(timeout=_timeout)

        if not ok:
            self._lifecycle.mark_failed(command, "Timeout")
            if self._lifecycle.can_retry(command):
                with self._lock:
                    self._lifecycle.prepare(command)
                    self._queue.append(command)
            else:
                self._dead_letter.append(command)
            with self._lock:
                self._total_failed += 1
        elif result[0] is not None:
            self._lifecycle.mark_failed(command, str(result[0]))
            if self._lifecycle.can_retry(command):
                with self._lock:
                    self._lifecycle.prepare(command)
                    self._queue.append(command)
            else:
                self._dead_letter.append(command)
            with self._lock:
                self._total_failed += 1
        else:
            self._lifecycle.mark_completed(command)
            with self._lock:
                self._total_dispatched += 1

        with self._lock:
            self._active -= 1

        return command

    @property
    def queue_size(self) -> int:
        return len(self._queue)

    @property
    def dead_letter_size(self) -> int:
        return len(self._dead_letter)

    def state(self) -> dict[str, Any]:
        with self._lock:
            return {
                "max_concurrency": self._max_concurrency,
                "active": self._active,
                "queue_size": self.queue_size,
                "dead_letter_size": self.dead_letter_size,
                "total_dispatched": self._total_dispatched,
                "total_failed": self._total_failed,
                "handlers": list(self._handlers.keys()),
            }
