from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class SafeCancellation:
    """Safe cancellation helper with cooperative cancellation support."""

    def __init__(self) -> None:
        self._cancelled = False
        self._lock = threading.RLock()
        self._callbacks: list[Callable[[], None]] = []

    def cancel(self) -> None:
        with self._lock:
            if self._cancelled:
                return
            self._cancelled = True
            callbacks = list(self._callbacks)
        for cb in callbacks:
            try:
                cb()
            except Exception:
                pass

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    def check(self) -> None:
        if self._cancelled:
            raise CancellationError("Operation was cancelled")

    def on_cancel(self, callback: Callable[[], None]) -> None:
        with self._lock:
            if self._cancelled:
                try:
                    callback()
                except Exception:
                    pass
                return
            self._callbacks.append(callback)

    def reset(self) -> None:
        with self._lock:
            self._cancelled = False
            self._callbacks.clear()


class CancellationError(Exception):
    """Raised when an operation is cancelled."""
