from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock


@dataclass
class QtRuntimeReport:
    scenario: str
    passed: bool
    duration_seconds: float = 0.0
    detail: str = ""
    leak_count: int = 0
    widget_count: int = 0


@dataclass
class LifecycleTrackedObject:
    id: str
    created_at: float
    destroyed: bool = False


class QtRuntimeHardener:
    def __init__(self) -> None:
        self._lock = Lock()
        self._objects: dict[str, LifecycleTrackedObject] = {}
        self._signal_subscriptions: dict[str, int] = {}
        self._render_count = 0
        self._dialog_stack: list[str] = []

    def create_object(self, obj_id: str) -> LifecycleTrackedObject:
        obj = LifecycleTrackedObject(id=obj_id, created_at=time.monotonic())
        with self._lock:
            self._objects[obj_id] = obj
        return obj

    def destroy_object(self, obj_id: str) -> bool:
        with self._lock:
            obj = self._objects.get(obj_id)
            if obj is None:
                return False
            obj.destroyed = True
            del self._objects[obj_id]
        return True

    def detect_orphans(
        self, max_age_seconds: float = 300.0,
    ) -> QtRuntimeReport:
        start = time.monotonic()
        now = time.monotonic()
        orphans: list[str] = []
        with self._lock:
            for oid, obj in list(self._objects.items()):
                if now - obj.created_at > max_age_seconds:
                    orphans.append(oid)
        passed = len(orphans) == 0
        return QtRuntimeReport(
            "orphan_detection", passed, time.monotonic() - start,
            f"orphans={len(orphans)}", leak_count=len(orphans),
        )

    def cleanup_orphans(self, max_age_seconds: float = 300.0) -> int:
        now = time.monotonic()
        removed = 0
        with self._lock:
            for oid, obj in list(self._objects.items()):
                if now - obj.created_at > max_age_seconds:
                    del self._objects[oid]
                    removed += 1
        return removed

    @property
    def tracked_count(self) -> int:
        with self._lock:
            return len(self._objects)

    def subscribe_signal(self, signal_name: str) -> None:
        with self._lock:
            self._signal_subscriptions[signal_name] = (
                self._signal_subscriptions.get(signal_name, 0) + 1
            )

    def unsubscribe_signal(self, signal_name: str) -> bool:
        with self._lock:
            cnt = self._signal_subscriptions.get(signal_name, 0)
            if cnt <= 0:
                return False
            if cnt == 1:
                del self._signal_subscriptions[signal_name]
            else:
                self._signal_subscriptions[signal_name] = cnt - 1
        return True

    def detect_signal_leaks(self) -> QtRuntimeReport:
        start = time.monotonic()
        total = sum(self._signal_subscriptions.values())
        passed = total == 0
        return QtRuntimeReport(
            "signal_leak", passed, time.monotonic() - start,
            f"active_subscriptions={total}", widget_count=total,
        )

    def record_render(self) -> None:
        self._render_count += 1

    def reset_render_count(self) -> None:
        self._render_count = 0

    @property
    def render_count(self) -> int:
        return self._render_count

    def open_dialog(self, dialog_id: str) -> None:
        with self._lock:
            self._dialog_stack.append(dialog_id)

    def close_dialog(self, dialog_id: str) -> bool:
        with self._lock:
            if self._dialog_stack and self._dialog_stack[-1] == dialog_id:
                self._dialog_stack.pop()
                return True
            return False

    @property
    def dialog_stack_size(self) -> int:
        with self._lock:
            return len(self._dialog_stack)

    def simulate_low_memory_render(
        self, memory_pressure: float,
    ) -> QtRuntimeReport:
        start = time.monotonic()
        blocked = memory_pressure > 0.85
        return QtRuntimeReport(
            "low_memory_render", not blocked,
            time.monotonic() - start,
            f"pressure={memory_pressure:.2f}, blocked={blocked}",
        )

    def simulate_long_session_widget_accumulation(
        self, cycles: int,
    ) -> QtRuntimeReport:
        start = time.monotonic()
        opened = 0
        closed = 0
        for i in range(cycles):
            self.create_object(f"widget_{i}")
            opened += 1
            if i % 2 == 0:
                self.destroy_object(f"widget_{i}")
                closed += 1
        leak = opened - closed
        return QtRuntimeReport(
            "long_session_widgets", leak <= 0,
            time.monotonic() - start,
            f"opened={opened}, closed={closed}, leak={leak}",
            widget_count=self.tracked_count,
        )
