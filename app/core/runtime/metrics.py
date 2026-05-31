from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Any


class RuntimeMetrics:
    """Lightweight runtime metrics collector."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}
        self._timings: dict[str, list[float]] = defaultdict(list)
        self._start_time = time.monotonic()

    def increment(self, name: str, value: int = 1) -> None:
        with self._lock:
            self._counters[name] += value

    def decrement(self, name: str, value: int = 1) -> None:
        with self._lock:
            self._counters[name] -= value

    def gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def record_timing(self, name: str, seconds: float) -> None:
        with self._lock:
            self._timings[name].append(seconds)
            if len(self._timings[name]) > 1000:
                self._timings[name] = self._timings[name][-1000:]

    def time(self, name: str) -> _TimerContext:
        return _TimerContext(self, name)

    @property
    def uptime(self) -> float:
        return time.monotonic() - self._start_time

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            timings_snapshot: dict[str, dict[str, float]] = {}
            for k, v in self._timings.items():
                if v:
                    timings_snapshot[k] = {
                        "min": min(v),
                        "max": max(v),
                        "avg": sum(v) / len(v),
                        "count": len(v),
                    }
                else:
                    timings_snapshot[k] = {"min": 0, "max": 0, "avg": 0, "count": 0}
            return {
                "uptime": self.uptime,
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "timings": timings_snapshot,
            }

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._timings.clear()
            self._start_time = time.monotonic()


class _TimerContext:
    def __init__(self, metrics: RuntimeMetrics, name: str) -> None:
        self._metrics = metrics
        self._name = name
        self._start: float | None = None

    def __enter__(self) -> _TimerContext:
        self._start = time.monotonic()
        return self

    def __exit__(self, *args: Any) -> None:
        if self._start is not None:
            elapsed = time.monotonic() - self._start
            self._metrics.record_timing(self._name, elapsed)
