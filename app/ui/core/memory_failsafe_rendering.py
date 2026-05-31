from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Generator

from app.ui.contracts.memory import MemoryContract, MemoryScope
from app.ui.contracts.rendering import BoundedRender


@dataclass
class MemoryAwareRenderGate:
    memory_contract: MemoryContract = field(default_factory=MemoryContract)
    render_bounds: BoundedRender = field(default_factory=BoundedRender)
    high_pressure_threshold: float = 0.85
    critical_pressure_threshold: float = 0.95
    current_widget_count: int = 0
    current_depth: int = 0
    render_blocked_count: int = 0
    render_allowed_count: int = 0
    pressure_level: str = "none"
    callbacks: list[Callable[[str], None]] = field(default_factory=list)

    def register_callback(self, cb: Callable[[str], None]) -> None:
        self.callbacks.append(cb)

    def _notify(self, event: str) -> None:
        for cb in self.callbacks:
            try:
                cb(event)
            except Exception:
                pass

    def update_pressure(self, current_memory_mb: float, max_memory_mb: int) -> None:
        ratio = current_memory_mb / max_memory_mb if max_memory_mb > 0 else 0
        if ratio >= self.critical_pressure_threshold:
            self.pressure_level = "critical"
        elif ratio >= self.high_pressure_threshold:
            self.pressure_level = "high"
        else:
            self.pressure_level = "none"

    def should_render(self, widget_count: int, depth: int) -> bool:
        if not self.render_bounds.within_bounds(widget_count, depth):
            self.render_blocked_count += 1
            self._notify("render_blocked_bounds")
            return False
        if self.pressure_level == "critical":
            self.render_blocked_count += 1
            self._notify("render_blocked_pressure")
            return False
        self.current_widget_count = widget_count
        self.current_depth = depth
        self.render_allowed_count += 1
        return True

    @contextmanager
    def gate(self, widget_count: int, depth: int) -> Generator[bool, Any, None]:
        allowed = self.should_render(widget_count, depth)
        try:
            yield allowed
        finally:
            pass

    def within_memory_limit(self, scope: MemoryScope, current: int) -> bool:
        return self.memory_contract.within_limit(scope, current)

    def scope_limit(self, scope: MemoryScope) -> int:
        return self.memory_contract.limit_for(scope)


def create_memory_failsafe_renderer(
    memory_contract: MemoryContract | None = None,
    render_bounds: BoundedRender | None = None,
) -> MemoryAwareRenderGate:
    return MemoryAwareRenderGate(
        memory_contract=memory_contract or MemoryContract(),
        render_bounds=render_bounds or BoundedRender(),
    )
