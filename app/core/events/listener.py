from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

from app.core.events.base import DomainEvent

EventListener = Callable[[DomainEvent], None]


class ListenerIsolation:
    """Bounded listener execution with timeout and error isolation."""

    def __init__(
        self,
        timeout: float = 10.0,
        name: str = "",
    ) -> None:
        self._timeout = timeout
        self._name = name
        self._lock = threading.RLock()
        self._total_calls = 0
        self._total_errors = 0
        self._total_timeouts = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def total_calls(self) -> int:
        return self._total_calls

    @property
    def total_errors(self) -> int:
        return self._total_errors

    @property
    def total_timeouts(self) -> int:
        return self._total_timeouts

    def execute(
        self,
        listener: EventListener,
        event: DomainEvent,
    ) -> None:
        result: list[Exception | None] = [None]
        event_obj = threading.Event()

        def _run() -> None:
            try:
                listener(event)
            except Exception as exc:
                result[0] = exc
            finally:
                event_obj.set()

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        ok = event_obj.wait(timeout=self._timeout)

        with self._lock:
            self._total_calls += 1
            if not ok:
                self._total_timeouts += 1
                raise TimeoutError(
                    f"Listener '{self._name}' timed out after {self._timeout}s"
                )
            if result[0] is not None:
                self._total_errors += 1
                raise result[0]  # type: ignore[misc]

    def state(self) -> dict[str, Any]:
        return {
            "name": self._name,
            "timeout": self._timeout,
            "total_calls": self._total_calls,
            "total_errors": self._total_errors,
            "total_timeouts": self._total_timeouts,
        }
