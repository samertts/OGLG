from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class EventBoundary:
    max_handlers_per_event: int = 20
    max_execution_ms: int = 100
    bubble_up: bool = True
    stop_propagation_on_error: bool = True
    allowed_event_types: tuple[str, ...] = (
        "navigation",
        "workflow",
        "dialog",
        "search",
        "archive",
        "draft",
        "print",
        "recovery",
        "sync",
        "audit",
    )

    def allows(self, event_type: str) -> bool:
        return event_type in self.allowed_event_types


class EventIsolationZone:
    def __init__(self, zone_id: str, boundary: EventBoundary | None = None):
        self._zone_id = zone_id
        self._boundary = boundary or EventBoundary()
        self._handlers: dict[str, list[Callable[[str, Any], None]]] = {}
        self._propagate_up: list[EventIsolationZone] = []

    @property
    def zone_id(self) -> str:
        return self._zone_id

    @property
    def boundary(self) -> EventBoundary:
        return self._boundary

    def register(self, event_type: str, handler: Callable[[str, Any], None]) -> None:
        if not self._boundary.allows(event_type):
            raise ValueError(f"Event type '{event_type}' not allowed in isolation zone")
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        limit = self._boundary.max_handlers_per_event
        if len(self._handlers[event_type]) >= limit:
            raise RuntimeError(f"Max handlers ({limit}) reached for {event_type}")
        self._handlers[event_type].append(handler)

    def emit(self, event_type: str, data: Any = None) -> None:
        if not self._boundary.allows(event_type):
            raise ValueError(f"Event type '{event_type}' not allowed")
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event_type, data)
            except Exception:
                if self._boundary.stop_propagation_on_error:
                    break

    def add_child_zone(self, zone: EventIsolationZone) -> None:
        self._propagate_up.append(zone)
