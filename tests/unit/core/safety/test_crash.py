from __future__ import annotations

import pytest

from app.core.safety.crash import CrashSafeWrapper, crash_safe, transaction_wrapper


def test_crash_safe_success() -> None:
    wrapper = CrashSafeWrapper()
    result = wrapper.run(lambda: 42)
    assert result == 42


def test_crash_safe_fallback() -> None:
    wrapper = CrashSafeWrapper(fallback=0)

    def fail() -> int:
        raise ValueError("boom")

    result = wrapper.run(fail)
    assert result == 0


def test_crash_safe_reraise() -> None:
    wrapper = CrashSafeWrapper(reraise=True)

    def fail() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        wrapper.run(fail)


def test_crash_safe_decorator() -> None:
    @crash_safe(fallback=-1)
    def divide(a: int, b: int) -> float:
        return a / b

    assert divide(10, 2) == 5.0
    assert divide(10, 0) == -1


def test_transaction_wrapper_commit() -> None:
    committed = False
    rolled_back = False

    def commit() -> None:
        nonlocal committed
        committed = True

    def rollback() -> None:
        nonlocal rolled_back
        rolled_back = True

    @transaction_wrapper(commit=commit, rollback=rollback)
    def ok() -> int:
        return 42

    result = ok()
    assert result == 42
    assert committed
    assert not rolled_back


def test_transaction_wrapper_rollback() -> None:
    committed = False
    rolled_back = False

    def commit() -> None:
        nonlocal committed
        committed = True

    def rollback() -> None:
        nonlocal rolled_back
        rolled_back = True

    @transaction_wrapper(commit=commit, rollback=rollback)
    def fail() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        fail()
    assert not committed
    assert rolled_back
