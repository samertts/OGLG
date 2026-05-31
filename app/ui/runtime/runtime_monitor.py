from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto


class MemoryPressureLevel(Enum):
    NONE = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


@dataclass
class RuntimeMetrics:
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    widget_count: int = 0
    active_tasks: int = 0
    pending_events: int = 0
    uptime_seconds: float = 0.0
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RuntimeMonitor:
    def __init__(self, max_widgets: int = 500, max_memory_mb: int = 1024):
        self._metrics = RuntimeMetrics()
        self._max_widgets = max_widgets
        self._max_memory_mb = max_memory_mb
        self._start_time = datetime.now(timezone.utc)
        self._pressure_level = MemoryPressureLevel.NONE

    def update(
        self,
        cpu: float | None = None,
        memory_mb: float | None = None,
        widget_count: int | None = None,
        active_tasks: int | None = None,
        pending_events: int | None = None,
    ) -> None:
        if cpu is not None:
            self._metrics.cpu_percent = cpu
        if memory_mb is not None:
            self._metrics.memory_mb = memory_mb
        if widget_count is not None:
            self._metrics.widget_count = widget_count
        if active_tasks is not None:
            self._metrics.active_tasks = active_tasks
        if pending_events is not None:
            self._metrics.pending_events = pending_events
        self._metrics.last_update = datetime.now(timezone.utc)
        self._recalc_pressure()

    def _recalc_pressure(self) -> None:
        max_mem = self._max_memory_mb or 1
        max_wid = self._max_widgets or 1
        mem_ratio = self._metrics.memory_mb / max_mem
        widget_ratio = self._metrics.widget_count / max_wid
        ratio = max(mem_ratio, widget_ratio)
        if ratio >= 0.9:
            self._pressure_level = MemoryPressureLevel.CRITICAL
        elif ratio >= 0.75:
            self._pressure_level = MemoryPressureLevel.HIGH
        elif ratio >= 0.5:
            self._pressure_level = MemoryPressureLevel.MEDIUM
        elif ratio >= 0.25:
            self._pressure_level = MemoryPressureLevel.LOW
        else:
            self._pressure_level = MemoryPressureLevel.NONE

    @property
    def metrics(self) -> RuntimeMetrics:
        delta = datetime.now(timezone.utc) - self._start_time
        self._metrics.uptime_seconds = delta.total_seconds()
        return self._metrics

    @property
    def pressure_level(self) -> MemoryPressureLevel:
        return self._pressure_level

    @property
    def in_pressure(self) -> bool:
        severe = (MemoryPressureLevel.MEDIUM, MemoryPressureLevel.HIGH,
                  MemoryPressureLevel.CRITICAL)
        return self._pressure_level in severe

    @property
    def is_critical(self) -> bool:
        return self._pressure_level == MemoryPressureLevel.CRITICAL
