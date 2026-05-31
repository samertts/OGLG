from __future__ import annotations

from app.core.events.base import DomainEvent, EventMetadata


def test_domain_event_immutable() -> None:
    event = DomainEvent(
        aggregate_id="agg-1",
        event_type="test.created",
        data={"key": "value"},
    )
    assert event.aggregate_id == "agg-1"
    assert event.event_type == "test.created"
    assert event.data == {"key": "value"}
    assert event.event_id is not None
    assert event.version == 1


def test_domain_event_to_dict() -> None:
    event = DomainEvent(
        aggregate_id="agg-1",
        event_type="test.created",
        data={"key": "value"},
    )
    d = event.to_dict()
    assert d["aggregate_id"] == "agg-1"
    assert d["event_type"] == "test.created"
    assert d["data"] == {"key": "value"}
    assert "event_id" in d
    assert "timestamp" in d


def test_domain_event_with_metadata() -> None:
    event = DomainEvent(
        aggregate_id="agg-1",
        event_type="test.updated",
        data={"field": "val"},
    )
    enriched = event.with_metadata(
        correlation_id="corr-1",
        causation_id="cause-1",
        source="test",
    )
    assert enriched.correlation_id == "corr-1"
    assert enriched.causation_id == "cause-1"
    assert enriched.metadata.source == "test"


def test_domain_event_replay_flag() -> None:
    meta = EventMetadata(replay=True)
    event = DomainEvent(
        aggregate_id="agg-1",
        event_type="test.replay",
        data={},
        metadata=meta,
    )
    assert event.is_replay
