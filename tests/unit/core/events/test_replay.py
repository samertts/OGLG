from __future__ import annotations

from pathlib import Path

from app.core.events.base import DomainEvent
from app.core.events.bus import EventBus
from app.core.events.replay import ReplayManager
from app.core.events.store import EventStore


def test_replay_from_checkpoint(tmp_path: Path) -> None:
    db = tmp_path / "replay.db"
    store = EventStore(db)
    store.open()
    bus = EventBus()
    rm = ReplayManager(store, bus, max_batch=10)

    store.append(
        DomainEvent(aggregate_id="a", event_type="test.evt", data={"n": 1})
    )
    store.append(
        DomainEvent(aggregate_id="a", event_type="test.evt", data={"n": 2})
    )

    rm.set_checkpoint("cp1")
    store.append(
        DomainEvent(aggregate_id="b", event_type="test.evt", data={"n": 3})
    )

    received: list[DomainEvent] = []

    def listener(event: DomainEvent) -> None:
        received.append(event)

    bus.subscribe("test.evt", listener)
    result = rm.replay_from_checkpoint("cp1", force=True)
    assert result["replayed"] == 1
    assert len(received) == 1
    store.close()


def test_replay_no_checkpoint(tmp_path: Path) -> None:
    db = tmp_path / "replay2.db"
    store = EventStore(db)
    store.open()
    bus = EventBus()
    rm = ReplayManager(store, bus)

    store.append(DomainEvent(aggregate_id="a", event_type="t", data={}))
    result = rm.replay_from_checkpoint("missing", force=False)
    assert result["replayed"] == 0
    store.close()


def test_replay_state(tmp_path: Path) -> None:
    db = tmp_path / "replay3.db"
    store = EventStore(db)
    store.open()
    bus = EventBus()
    rm = ReplayManager(store, bus)
    state = rm.state()
    assert state["max_batch"] == 1000
    store.close()
