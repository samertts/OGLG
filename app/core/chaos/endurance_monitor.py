from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from threading import Lock


@dataclass
class EnduranceReport:
    memory_mb_delta: float = 0.0
    memory_exceeded: bool = False
    event_listener_count: int = 0
    event_leak_detected: bool = False
    orphan_task_count: int = 0
    orphan_task_exceeded: bool = False
    queue_depth: int = 0
    queue_exceeded: bool = False
    wal_mb_growth: float = 0.0
    wal_exceeded: bool = False
    async_exhaustion_count: int = 0
    async_exhausted: bool = False
    duration_seconds: float = 0.0
    passed: bool = False


class EnduranceMonitor:
    MAX_MEMORY_MB = 500.0
    MAX_EVENT_LISTENERS = 500
    MAX_ORPHAN_TASKS = 100
    MAX_QUEUE_DEPTH = 1000
    MAX_WAL_MB = 200.0
    MAX_ASYNC_EXHAUSTION = 200
    CHECK_INTERVAL_24H = 86400
    CHECK_INTERVAL_72H = 259200

    def __init__(
        self,
        db_path: str | Path | None = None,
        max_memory_mb: float | None = None,
        max_event_listeners: int | None = None,
        max_orphan_tasks: int | None = None,
        max_queue_depth: int | None = None,
        max_wal_mb: float | None = None,
        max_async_exhaustion: int | None = None,
    ) -> None:
        self._db_path = Path(db_path) if db_path else Path("/dev/null")
        self._lock = Lock()
        self._max_memory_mb = max_memory_mb if max_memory_mb is not None else self.MAX_MEMORY_MB
        self._max_event_listeners = max_event_listeners or self.MAX_EVENT_LISTENERS
        self._max_orphan_tasks = max_orphan_tasks or self.MAX_ORPHAN_TASKS
        self._max_queue_depth = max_queue_depth or self.MAX_QUEUE_DEPTH
        self._max_wal_mb = max_wal_mb if max_wal_mb is not None else self.MAX_WAL_MB
        self._max_async_exhaustion = max_async_exhaustion or self.MAX_ASYNC_EXHAUSTION
        self._free_wal_space_mb: float = 0.0
        self._orphan_tasks: list[str] = []
        self._start_time = time.monotonic()
        self._last_check_24h = 0.0
        self._last_check_72h = 0.0

    def check_memory_growth(self, current_mb: float, baseline_mb: float = 0.0) -> EnduranceReport:
        delta = current_mb - baseline_mb
        report = EnduranceReport(
            memory_mb_delta=delta,
            memory_exceeded=delta > self._max_memory_mb,
        )
        report.passed = not report.memory_exceeded
        return report

    def check_event_listener_leak(self, listener_count: int) -> EnduranceReport:
        report = EnduranceReport(
            event_listener_count=listener_count,
            event_leak_detected=listener_count > self._max_event_listeners,
        )
        report.passed = not report.event_leak_detected
        return report

    def check_orphan_tasks(self) -> EnduranceReport:
        count = len(self._orphan_tasks)
        report = EnduranceReport(
            orphan_task_count=count,
            orphan_task_exceeded=count > self._max_orphan_tasks,
        )
        report.passed = not report.orphan_task_exceeded
        return report

    def check_queue_growth(self, depth: int) -> EnduranceReport:
        report = EnduranceReport(
            queue_depth=depth,
            queue_exceeded=depth > self._max_queue_depth,
        )
        report.passed = not report.queue_exceeded
        return report

    def check_wal_growth(self, wal_mb: float) -> EnduranceReport:
        delta = wal_mb - self._free_wal_space_mb
        report = EnduranceReport(
            wal_mb_growth=delta,
            wal_exceeded=delta > self._max_wal_mb,
        )
        report.passed = not report.wal_exceeded
        return report

    def check_async_exhaustion(self, pending_count: int) -> EnduranceReport:
        report = EnduranceReport(
            async_exhaustion_count=pending_count,
            async_exhausted=pending_count > self._max_async_exhaustion,
        )
        report.passed = not report.async_exhausted
        return report

    def check_24h_runtime(self) -> EnduranceReport:
        elapsed = time.monotonic() - self._start_time
        check_due = (elapsed - self._last_check_24h) >= self.CHECK_INTERVAL_24H
        if check_due:
            self._last_check_24h += self.CHECK_INTERVAL_24H
        report = EnduranceReport(duration_seconds=elapsed)
        report.passed = check_due
        return report

    def check_72h_runtime(self) -> EnduranceReport:
        elapsed = time.monotonic() - self._start_time
        check_due = (elapsed - self._last_check_72h) >= self.CHECK_INTERVAL_72H
        if check_due:
            self._last_check_72h += self.CHECK_INTERVAL_72H
        report = EnduranceReport(duration_seconds=elapsed)
        report.passed = check_due
        return report

    def record_orphan_task(self, task_id: str) -> None:
        with self._lock:
            self._orphan_tasks.append(task_id)

    def cleanup(self) -> None:
        self._orphan_tasks.clear()

    def reset_free_wal_space(self, mb: float) -> None:
        self._free_wal_space_mb = mb
