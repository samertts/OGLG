from __future__ import annotations

import time

import pytest

from app.core.safety.guards import BoundedExecutionGuard, timeout_wrapper


def test_bounded_guard_success() -> None:
    guard = BoundedExecutionGuard(default_timeout=5.0)
    result = guard.run(lambda: 42)
    assert result == 42


def test_bounded_guard_timeout() -> None:
    guard = BoundedExecutionGuard(default_timeout=0.1)

    def slow() -> None:
        time.sleep(10.0)

    with pytest.raises(TimeoutError):
        guard.run(slow)


def test_bounded_guard_error_propagation() -> None:
    guard = BoundedExecutionGuard(default_timeout=5.0)

    def fail() -> None:
        raise ValueError("test error")

    with pytest.raises(ValueError, match="test error"):
        guard.run(fail)


def test_timeout_wrapper_decorator() -> None:
    @timeout_wrapper(timeout=5.0)
    def add(a: int, b: int) -> int:
        return a + b

    assert add(1, 2) == 3
