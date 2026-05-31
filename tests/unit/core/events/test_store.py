from __future__ import annotations

from pathlib import Path

from app.core.events.base import DomainEvent
from app.core.events.store import EventStore


def test_store_open_and_append(tmp_path: Path) -> None:
    db = tmp_path / "events.db"
    store = EventStore(db)
    store.open()
    event = DomainEvent(
        aggregate_id="agg-1",
        event_type="test.created",
        data={"key": "val"},
    )
    seq = store.append(event)
    assert seq == 1
    assert store.max_sequence == 1
    assert store.event_count == 1
    store.close()


def test_store_read_since(tmp_path: Path) -> None:
    db = tmp_path / "events.db"
    store = EventStore(db)
    store.open()
    e1 = DomainEvent(aggregate_id="agg-1", event_type="t.1", data={"n": 1})
    e2 = DomainEvent(aggregate_id="agg-1", event_type="t.2", data={"n": 2})
    store.append(e1)
    store.append(e2)
    events = store.read_since(0)
    assert len(events) == 2
    assert events[0].event_type == "t.1"
    assert events[1].event_type == "t.2"
    store.close()


def test_store_read_by_type(tmp_path: Path) -> None:
    db = tmp_path / "events.db"
    store = EventStore(db)
    store.open()
    store.append(DomainEvent(aggregate_id="a", event_type="type.a", data={}))
    store.append(DomainEvent(aggregate_id="b", event_type="type.b", data={}))
    type_a = store.read_by_type("type.a")
    assert len(type_a) == 1
    assert type_a[0].event_type == "type.a"
    store.close()


def test_store_read_by_aggregate(tmp_path: Path) -> None:
    db = tmp_path / "events.db"
    store = EventStore(db)
    store.open()
    store.append(DomainEvent(aggregate_id="agg-1", event_type="t.1", data={}))
    store.append(DomainEvent(aggregate_id="agg-2", event_type="t.2", data={}))
    agg_events = store.read_by_aggregate("agg-1")
    assert len(agg_events) == 1
    store.close()


def test_store_checkpoint(tmp_path: Path) -> None:
    db = tmp_path / "events.db"
    store = EventStore(db)
    store.open()
    store.append(DomainEvent(aggregate_id="a", event_type="t", data={}))
    store.append(DomainEvent(aggregate_id="a", event_type="t", data={}))
    store.save_checkpoint("cp1")
    seq = store.load_checkpoint("cp1")
    assert seq == 2
    store.close()


def test_store_reopen_preserves_sequence(tmp_path: Path) -> None:
    db = tmp_path / "events.db"
    store = EventStore(db)
    store.open()
    store.append(DomainEvent(aggregate_id="a", event_type="t", data={}))
    seq1 = store.max_sequence
    store.close()

    store2 = EventStore(db)
    store2.open()
    assert store2.max_sequence == seq1
    assert store2.event_count == 1
    store2.close()


def test_store_state(tmp_path: Path) -> None:
    db = tmp_path / "events.db"
    store = EventStore(db)
    store.open()
    state = store.state()
    assert state["open"] is True
    assert "path" in state
    store.close()
