from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Generator


@dataclass
class WindowGuard:
    allow_close: bool = True
    close_handler: Callable[[], bool] | None = None
    error_handler: Callable[[Exception], None] | None = None
    crash_count: int = 0
    max_crashes: int = 5
    metadata: dict[str, Any] = field(default_factory=dict)


class CrashSafeWindow:
    def __init__(self, window_id: str, guard: WindowGuard | None = None):
        self._window_id = window_id
        self._guard = guard or WindowGuard()
        self._open = False
        self._shutdown_requested = False

    @property
    def window_id(self) -> str:
        return self._window_id

    @property
    def is_open(self) -> bool:
        return self._open

    @property
    def guard(self) -> WindowGuard:
        return self._guard

    @contextmanager
    def protect(self) -> Generator[None, Any, None]:
        try:
            yield
        except Exception as e:
            self._guard.crash_count += 1
            if self._guard.error_handler:
                self._guard.error_handler(e)
            if self._guard.crash_count >= self._guard.max_crashes:
                self.request_shutdown()

    def open(self) -> None:
        self._open = True

    def close(self) -> bool:
        if self._guard.close_handler and not self._guard.close_handler():
            return False
        self._open = False
        return True

    def request_shutdown(self) -> None:
        self._shutdown_requested = True

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown_requested
