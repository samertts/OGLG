from __future__ import annotations

import time

import pytest

from app.ui.core.performance_hardening import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    OperationTimeout,
    PerformanceHardener,
)


class TestCircuitBreaker:
    def test_initial_state_closed(self):
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED

    def test_trips_after_threshold_failures(self):
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=3))
        def _fail() -> None:
            raise ValueError("fail")
        for _ in range(3):
            with pytest.raises(ValueError):
                cb.call(_fail)
        assert cb.state == CircuitState.OPEN

    def test_recovers_after_timeout(self):
        cfg = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.01)
        cb = CircuitBreaker(cfg)
        def _fail() -> None:
            raise ValueError("fail")
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(_fail)
        assert cb.state == CircuitState.OPEN
        time.sleep(0.02)
        def _ok() -> str:
            return "ok"
        result = cb.call(_ok)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    def test_half_open_limits_calls(self):
        cfg = CircuitBreakerConfig(
            failure_threshold=2, recovery_timeout=0.01,
            half_open_max_calls=1,
        )
        cb = CircuitBreaker(cfg)
        def _fail() -> None:
            raise ValueError("fail")
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(_fail)
        time.sleep(0.02)
        def _ok() -> str:
            return "ok"
        result = cb.call(_ok)
        assert result == "ok"
        assert cb.state == CircuitState.CLOSED

    def test_stats(self):
        cb = CircuitBreaker(CircuitBreakerConfig(name="test"))
        assert cb.stats["name"] == "test"
        assert cb.stats["state"] == "CLOSED"

    def test_reset(self):
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=1))
        def _fail() -> None:
            raise ValueError("fail")
        with pytest.raises(ValueError):
            cb.call(_fail)
        assert cb.state == CircuitState.OPEN
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0

    def test_set_state_change_callback(self):
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=1))
        changes: list[tuple[CircuitState, CircuitState]] = []
        cb.set_state_change_callback(lambda o, n: changes.append((o, n)))
        def _fail() -> None:
            raise ValueError("fail")
        with pytest.raises(ValueError):
            cb.call(_fail)
        assert len(changes) == 1
        assert changes[0] == (CircuitState.CLOSED, CircuitState.OPEN)


class TestOperationTimeout:
    def test_returns_result(self):
        ot = OperationTimeout(max_seconds=5.0)
        result = ot.execute(lambda: 42)
        assert result == 42

    def test_raises_on_timeout(self):
        ot = OperationTimeout(max_seconds=0.01, raise_on_timeout=True)
        def _slow() -> None:
            time.sleep(10)
        with pytest.raises(TimeoutError):
            ot.execute(_slow)

    def test_returns_none_on_timeout_no_raise(self):
        ot = OperationTimeout(max_seconds=0.01, raise_on_timeout=False)
        def _slow() -> None:
            time.sleep(10)
        assert ot.execute(_slow) is None

    def test_reraises_exception(self):
        ot = OperationTimeout(max_seconds=5.0)
        def _fail() -> None:
            raise ValueError("ops")
        with pytest.raises(ValueError):
            ot.execute(_fail)


class TestPerformanceHardener:
    def test_register_breaker(self):
        ph = PerformanceHardener()
        cb = ph.register_breaker("db_query")
        assert cb is ph.get_breaker("db_query")

    def test_register_timeout(self):
        ph = PerformanceHardener()
        ot = ph.register_timeout("slow_op", 5.0)
        assert ot is ph.get_timeout("slow_op")

    def test_protected_call_passes_through(self):
        ph = PerformanceHardener()
        result = ph.protected_call("nonexistent", lambda: 99)
        assert result == 99

    def test_protected_call_with_breaker(self):
        ph = PerformanceHardener()
        ph.register_breaker("test", CircuitBreakerConfig(failure_threshold=2))
        def _ok() -> str:
            return "done"
        result = ph.protected_call("test", _ok)
        assert result == "done"

    def test_timed_call_passes_through(self):
        ph = PerformanceHardener()
        result = ph.timed_call("nonexistent", lambda: 77)
        assert result == 77

    def test_timed_call_with_timeout(self):
        ph = PerformanceHardener()
        ph.register_timeout("fast", 5.0)
        result = ph.timed_call("fast", lambda: 33)
        assert result == 33

    def test_reset_all(self):
        ph = PerformanceHardener()
        cb = ph.register_breaker("test", CircuitBreakerConfig(failure_threshold=1))
        def _fail() -> None:
            raise ValueError("fail")
        with pytest.raises(ValueError):
            ph.protected_call("test", _fail)
        assert cb.state == CircuitState.OPEN
        ph.reset_all()
        assert cb.state == CircuitState.CLOSED

    def test_stats(self):
        ph = PerformanceHardener()
        ph.register_breaker("b1")
        ph.register_timeout("t1", 1.0)
        stats = ph.stats
        assert "breakers" in stats
        assert "timeouts" in stats
        assert "b1" in stats["breakers"]

    def test_failure_count_tracks(self):
        ph = PerformanceHardener()
        ph.register_breaker("test", CircuitBreakerConfig(failure_threshold=1))
        def _fail() -> None:
            raise ValueError("fail")
        with pytest.raises(ValueError):
            ph.protected_call("test", _fail)
        assert ph._failure_count == 1
