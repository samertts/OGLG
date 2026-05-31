from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass
class LazyMount:
    widget_id: str
    factory: Callable[[], Any]
    mounted: bool = False
    mounted_at: datetime | None = None

    def resolve(self) -> Any:
        if not self.mounted:
            return None
        return self.factory()


class TaskScheduler:
    def __init__(self):
        self._mounts: dict[str, LazyMount] = {}
        self._scheduled: list[tuple[str, Callable[[], None], float]] = []

    def register_mount(self, widget_id: str, factory: Callable[[], Any]) -> LazyMount:
        mount = LazyMount(widget_id=widget_id, factory=factory)
        self._mounts[widget_id] = mount
        return mount

    def mount(self, widget_id: str) -> Any:
        mount = self._mounts.get(widget_id)
        if mount is None:
            raise KeyError(f"No lazy mount registered for: {widget_id}")
        if not mount.mounted:
            mount.mounted = True
            mount.mounted_at = datetime.now(timezone.utc)
        return mount.factory()

    def is_mounted(self, widget_id: str) -> bool:
        mount = self._mounts.get(widget_id)
        if mount is None:
            return False
        return mount.mounted

    def schedule(self, task_id: str, fn: Callable[[], None], delay_ms: float = 0) -> None:
        self._scheduled.append((task_id, fn, delay_ms))

    @property
    def mount_count(self) -> int:
        return len(self._mounts)
