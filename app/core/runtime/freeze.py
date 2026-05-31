from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any


class FreezeWatchdog:
    """Runtime freeze detection watchdog hooks.

    Monitors a heartbeat signal and triggers callbacks
    if no heartbeat is received within the deadline.
    """

    def __init__(
        self,
        timeout: float = 5.0,
        check_interval: float = 1.0,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be > 0")
        if check_interval <= 0:
            raise ValueError("check_interval must be > 0")
        self._timeout = timeout
        self._check_interval = check_interval
        self._last_heartbeat = time.monotonic()
        self._frozen = False
        self._lock = threading.RLock()
        self._callbacks: list[Callable[[float], None]] = []
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def heartbeat(self) -> None:
        with self._lock:
            self._last_heartbeat = time.monotonic()
            self._frozen = False

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    @property
    def seconds_since_heartbeat(self) -> float:
        return time.monotonic() - self._last_heartbeat

    def on_freeze(self, callback: Callable[[float], None]) -> None:
        with self._lock:
            self._callbacks.append(callback)

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=3.0)
            self._thread = None

    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            elapsed = self.seconds_since_heartbeat
            if elapsed > self._timeout and not self._frozen:
                with self._lock:
                    self._frozen = True
                for cb in self._callbacks:
                    try:
                        cb(elapsed)
                    except Exception:
                        pass
            self._stop_event.wait(timeout=self._check_interval)

    def state(self) -> dict[str, Any]:
        return {
            "timeout": self._timeout,
            "check_interval": self._check_interval,
            "frozen": self._frozen,
            "seconds_since_heartbeat": self.seconds_since_heartbeat,
            "running": self._thread is not None and self._thread.is_alive(),
        }
