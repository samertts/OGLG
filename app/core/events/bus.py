from __future__ import annotations

import threading
from typing import Any

from app.core.events.base import DomainEvent
from app.core.events.listener import EventListener, ListenerIsolation


class EventBus:
    """Internal event bus with typed dispatching, isolation, and replay safety."""

    def __init__(self, listener_timeout: float = 10.0) -> None:
        self._listeners: dict[str, list[tuple[EventListener, int, bool]]] = {}
        self._lock = threading.RLock()
        self._delivered: set[str] = set()
        self._sequence = 0
        self._listener_timeout = listener_timeout
        self._isolations: dict[str, ListenerIsolation] = {}
        self._dispatch_in_progress = False

    def subscribe(
        self,
        event_type: str,
        listener: EventListener,
        priority: int = 0,
        deduplicate: bool = True,
    ) -> None:
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            self._listeners[event_type].append(
                (listener, priority, deduplicate)
            )
            self._listeners[event_type].sort(
                key=lambda x: x[1], reverse=True
            )
            iso_name = f"{event_type}_{len(self._listeners[event_type])}"
            self._isolations[iso_name] = ListenerIsolation(
                timeout=self._listener_timeout,
                name=iso_name,
            )

    def unsubscribe_all(self, event_type: str) -> None:
        with self._lock:
            self._listeners.pop(event_type, None)

    def publish(
        self,
        event: DomainEvent,
        source: str = "",
    ) -> list[str]:
        dispatched: list[str] = []
        dedup_key = event.event_id

        with self._lock:
            if dedup_key in self._delivered:
                return dispatched
            self._sequence += 1
            seq = self._sequence
            if event.metadata.sequence == 0 and not event.metadata.replay:
                meta = event.metadata
                object.__setattr__(meta, "sequence", seq)
                object.__setattr__(meta, "replay", False)
            elif event.metadata.sequence == 0 and event.metadata.replay:
                meta = event.metadata
                object.__setattr__(meta, "sequence", seq)
            self._delivered.add(dedup_key)

            event_type = event.event_type
            listeners = list(
                self._listeners.get(event_type, [])
            )
            wildcard = list(
                self._listeners.get("*", [])
            )

        all_listeners = listeners + wildcard

        for listener, _, use_dedup in all_listeners:
            iso_name = f"{event_type}_{id(listener)}"
            iso = self._isolations.get(
                iso_name,
                ListenerIsolation(
                    timeout=self._listener_timeout,
                    name=iso_name,
                ),
            )
            try:
                iso.execute(listener, event)
                dispatched.append(event.event_id)
            except Exception:
                pass

        return dispatched

    def replay(
        self,
        events: list[DomainEvent],
    ) -> list[str]:
        dispatched: list[str] = []
        for event in events:
            meta = event.metadata
            object.__setattr__(meta, "replay", True)
            dispatched.extend(self.publish(event, source="replay"))
        return dispatched

    def has_delivered(self, event_id: str) -> bool:
        with self._lock:
            return event_id in self._delivered

    def listener_count(self, event_type: str = "") -> int:
        with self._lock:
            if event_type:
                return len(self._listeners.get(event_type, []))
            return sum(len(v) for v in self._listeners.values())

    @property
    def sequence(self) -> int:
        return self._sequence

    def state(self) -> dict[str, Any]:
        with self._lock:
            return {
                "sequence": self._sequence,
                "delivered_count": len(self._delivered),
                "event_types": list(self._listeners.keys()),
                "listener_count": self.listener_count(),
            }
