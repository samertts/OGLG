from __future__ import annotations

import pytest

from app.core.safety.cancellation import CancellationError, SafeCancellation


def test_cancellation_not_cancelled() -> None:
    c = SafeCancellation()
    assert not c.is_cancelled
    c.check()


def test_cancellation_cancel() -> None:
    c = SafeCancellation()
    c.cancel()
    assert c.is_cancelled
    with pytest.raises(CancellationError):
        c.check()


def test_cancellation_on_cancel() -> None:
    c = SafeCancellation()
    triggered = []

    def cb() -> None:
        triggered.append("called")

    c.on_cancel(cb)
    assert len(triggered) == 0
    c.cancel()
    assert len(triggered) == 1


def test_cancellation_on_cancel_after_cancel() -> None:
    c = SafeCancellation()
    triggered = []

    def cb() -> None:
        triggered.append("called")

    c.cancel()
    c.on_cancel(cb)
    assert len(triggered) == 1


def test_cancellation_reset() -> None:
    c = SafeCancellation()
    c.cancel()
    assert c.is_cancelled
    c.reset()
    assert not c.is_cancelled
    c.check()
