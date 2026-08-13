from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.core.events.base import DomainEvent, EventMetadata
from app.integration.gula_publisher import GulaEventPublisher


class FakeResponse:
    status = 202

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeOpener:
    def __init__(self):
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        return FakeResponse()


def test_publisher_emits_correspondence_envelope():
    opener = FakeOpener()
    event = DomainEvent(
        aggregate_id="letter-1",
        event_type="LETTER_ISSUED",
        data={"subject": "administrative"},
        metadata=EventMetadata(
            id="event-1",
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            source="operator-1",
        ),
    )

    GulaEventPublisher("https://gula.example", "token", "tenant-1", opener=opener).publish(event)

    request, timeout = opener.requests[0]
    assert timeout == 10
    assert request.get_header("Authorization") == "Bearer token"
    assert b'"event_type": "correspondence.issued"' in request.data
    assert b'"tenant_id": "tenant-1"' in request.data
    assert b'"idempotency_key"' in request.data


def test_publisher_requires_explicit_configuration():
    with pytest.raises(ValueError):
        GulaEventPublisher("", "token", "tenant").publish(SimpleNamespace())
