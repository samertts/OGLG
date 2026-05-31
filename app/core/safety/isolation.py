from __future__ import annotations

import gc
import logging
import os
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class MemoryPressureGuard:
    """Memory pressure protection monitor.

    Tracks and warns when memory usage exceeds configured thresholds.
    """

    def __init__(
        self,
        warning_mb: float = 500.0,
        critical_mb: float = 800.0,
        check_interval: float = 10.0,
    ) -> None:
        if warning_mb >= critical_mb:
            raise ValueError("warning_mb must be < critical_mb")
        self._warning_mb = warning_mb
        self._critical_mb = critical_mb
        self._check_interval = check_interval
        self._lock = threading.RLock()
        self._callbacks: dict[str, Callable[[dict[str, Any]], None]] = {}
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_check: float = 0.0

    @property
    def warning_mb(self) -> float:
        return self._warning_mb

    @property
    def critical_mb(self) -> float:
        return self._critical_mb

    def on_pressure(
        self, name: str, callback: Callable[[dict[str, Any]], None]
    ) -> None:
        with self._lock:
            self._callbacks[name] = callback

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
            self._check_pressure()
            self._stop_event.wait(timeout=self._check_interval)

    def _check_pressure(self) -> None:
        usage = self._get_memory_usage()
        if usage is None:
            return
        level = "ok"
        if usage["rss_mb"] >= self._critical_mb:
            level = "critical"
            gc.collect()
        elif usage["rss_mb"] >= self._warning_mb:
            level = "warning"
        if level != "ok":
            usage["level"] = level
            with self._lock:
                for cb in self._callbacks.values():
                    try:
                        cb(usage)
                    except Exception:
                        pass

    @staticmethod
    def _get_memory_usage() -> dict[str, Any] | None:
        try:
            import psutil

            process = psutil.Process(os.getpid())
            mem = process.memory_info()
            return {
                "rss_mb": mem.rss / (1024 * 1024),
                "vms_mb": mem.vms / (1024 * 1024),
                "rss": mem.rss,
                "vms": mem.vms,
            }
        except ImportError:
            pass
        try:
            with open(f"/proc/{os.getpid()}/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        parts = line.split()
                        rss_kb = int(parts[1])
                        return {
                            "rss_mb": rss_kb / 1024,
                            "vms_mb": 0,
                            "rss": rss_kb * 1024,
                            "vms": 0,
                        }
        except OSError:
            pass
        return None

    def state(self) -> dict[str, Any]:
        usage = self._get_memory_usage() or {}
        return {
            "warning_mb": self._warning_mb,
            "critical_mb": self._critical_mb,
            "current": usage,
            "running": self._thread is not None and self._thread.is_alive(),
        }


class SubsystemIsolation:
    """Subsystem execution boundary with resource tracking."""

    def __init__(self, name: str) -> None:
        if not name:
            raise ValueError("name must not be empty")
        self._name = name
        self._lock = threading.RLock()
        self._active = 0
        self._total_calls = 0
        self._total_errors = 0
        self._start_time = time.monotonic()

    @property
    def name(self) -> str:
        return self._name

    def execute(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        with self._lock:
            self._active += 1
            self._total_calls += 1
        try:
            return func(*args, **kwargs)
        except Exception:
            with self._lock:
                self._total_errors += 1
            raise
        finally:
            with self._lock:
                self._active -= 1

    @property
    def active(self) -> int:
        return self._active

    @property
    def total_calls(self) -> int:
        return self._total_calls

    @property
    def total_errors(self) -> int:
        return self._total_errors

    @property
    def uptime(self) -> float:
        return time.monotonic() - self._start_time

    @property
    def error_rate(self) -> float:
        if self._total_calls == 0:
            return 0.0
        return self._total_errors / self._total_calls

    def state(self) -> dict[str, Any]:
        return {
            "name": self._name,
            "active": self._active,
            "total_calls": self._total_calls,
            "total_errors": self._total_errors,
            "error_rate": self.error_rate,
            "uptime": self.uptime,
        }


def subsystem_boundary(name: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that wraps a function in a subsystem isolation boundary."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        isolation = SubsystemIsolation(name)

        def wrapper(*args: Any, **kwargs: Any) -> T:
            return isolation.execute(func, *args, **kwargs)

        return wrapper

    return decorator
