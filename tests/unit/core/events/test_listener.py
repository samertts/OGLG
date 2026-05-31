from __future__ import annotations

import time

import pytest

from app.core.events.base import DomainEvent
from app.core.events.listener import ListenerIsolation


def test_listener_isolation_success() -> None:
    iso = ListenerIsolation(timeout=5.0, name="test")
    received: list[str] = []

    def listener(event: DomainEvent) -> None:
        received.append(event.event_id)

    event = DomainEvent(aggregate_id="a", event_type="t", data={})
    iso.execute(listener, event)
    assert len(received) == 1


def test_listener_isolation_timeout() -> None:
    iso = ListenerIsolation(timeout=0.1, name="slow")

    def listener(event: DomainEvent) -> None:
        time.sleep(10.0)

    event = DomainEvent(aggregate_id="a", event_type="t", data={})
    with pytest.raises(TimeoutError):
        iso.execute(listener, event)
    assert iso.total_timeouts == 1


def test_listener_isolation_error() -> None:
    iso = ListenerIsolation(timeout=5.0, name="failing")

    def listener(event: DomainEvent) -> None:
        raise ValueError("listener error")

    event = DomainEvent(aggregate_id="a", event_type="t", data={})
    with pytest.raises(ValueError):
        iso.execute(listener, event)
    assert iso.total_errors == 1


def test_listener_isolation_state() -> None:
    iso = ListenerIsolation(timeout=5.0, name="test-state")
    state = iso.state()
    assert state["name"] == "test-state"
    assert state["total_calls"] == 0
