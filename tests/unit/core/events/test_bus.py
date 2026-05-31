from __future__ import annotations

from app.core.events.base import DomainEvent
from app.core.events.bus import EventBus


def test_event_bus_publish_subscribe() -> None:
    bus = EventBus()
    received: list[DomainEvent] = []

    def listener(event: DomainEvent) -> None:
        received.append(event)

    bus.subscribe("test.event", listener)
    event = DomainEvent(
        aggregate_id="agg-1",
        event_type="test.event",
        data={"key": "val"},
    )
    bus.publish(event)
    assert len(received) == 1
    assert received[0].event_id == event.event_id


def test_event_bus_deduplication() -> None:
    bus = EventBus()
    count = 0

    def listener(event: DomainEvent) -> None:
        nonlocal count
        count += 1

    bus.subscribe("test.event", listener)
    event = DomainEvent(
        aggregate_id="agg-1",
        event_type="test.event",
        data={},
    )
    bus.publish(event)
    bus.publish(event)
    assert count == 1


def test_event_bus_no_listener() -> None:
    bus = EventBus()
    event = DomainEvent(
        aggregate_id="agg-1",
        event_type="unhandled",
        data={},
    )
    result = bus.publish(event)
    assert result == []


def test_event_bus_wildcard() -> None:
    bus = EventBus()
    received: list[str] = []

    def listener(event: DomainEvent) -> None:
        received.append(event.event_type)

    bus.subscribe("*", listener)
    e1 = DomainEvent(aggregate_id="a", event_type="type.a", data={})
    e2 = DomainEvent(aggregate_id="b", event_type="type.b", data={})
    bus.publish(e1)
    bus.publish(e2)
    assert "type.a" in received
    assert "type.b" in received


def test_event_bus_replay() -> None:
    bus = EventBus()
    received: list[DomainEvent] = []

    def listener(event: DomainEvent) -> None:
        received.append(event)

    bus.subscribe("test.event", listener)
    event = DomainEvent(
        aggregate_id="agg-1",
        event_type="test.event",
        data={},
    )
    bus.replay([event])
    assert len(received) == 1
    assert received[0].is_replay


def test_event_bus_state() -> None:
    bus = EventBus()

    def listener(event: DomainEvent) -> None:
        pass

    bus.subscribe("test.a", listener)
    bus.subscribe("test.b", listener)
    state = bus.state()
    assert state["event_types"] == ["test.a", "test.b"]
    assert state["listener_count"] == 2
