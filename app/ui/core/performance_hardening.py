from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum, auto
from threading import Lock
from typing import Any, Callable


class CircuitState(Enum):
    CLOSED = auto()
    OPEN = auto()
    HALF_OPEN = auto()


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3
    name: str = ""


class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        self._config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = Lock()
        self._total_calls = 0
        self._total_failures = 0
        self._total_timeouts = 0
        self._on_state_change: Callable[[CircuitState, CircuitState], None] | None = None

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    def set_state_change_callback(self, cb: Callable[[CircuitState, CircuitState], None]) -> None:
        self._on_state_change = cb

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        with self._lock:
            self._total_calls += 1
            if self._state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    self._transition(CircuitState.HALF_OPEN)
                else:
                    raise RuntimeError(
                        f"Circuit breaker '{self._config.name}' is OPEN"
                    )
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self._config.half_open_max_calls:
                    raise RuntimeError(
                        f"Circuit breaker '{self._config.name}' half-open max calls exceeded"
                    )
                self._half_open_calls += 1
        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _should_attempt_recovery(self) -> bool:
        if self._last_failure_time is None:
            return True
        elapsed = time.monotonic() - self._last_failure_time
        return elapsed >= self._config.recovery_timeout

    def _on_success(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._transition(CircuitState.CLOSED)
                self._half_open_calls = 0
            self._failure_count = 0

    def _on_failure(self) -> None:
        with self._lock:
            self._total_failures += 1
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self._config.failure_threshold:
                if self._state != CircuitState.OPEN:
                    self._transition(CircuitState.OPEN)

    def _transition(self, new_state: CircuitState) -> None:
        old = self._state
        self._state = new_state
        if self._on_state_change:
            self._on_state_change(old, new_state)

    def reset(self) -> None:
        with self._lock:
            self._transition(CircuitState.CLOSED)
            self._failure_count = 0
            self._half_open_calls = 0

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "name": self._config.name,
            "state": self._state.name,
            "failure_count": self._failure_count,
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
            "total_timeouts": self._total_timeouts,
        }


@dataclass
class OperationTimeout:
    operation_name: str = ""
    max_seconds: float = 10.0
    raise_on_timeout: bool = True

    def execute(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        from threading import Event, Thread

        result: list[Any] = [None]
        error: list[Exception | None] = [None]
        done = Event()

        def _run() -> None:
            try:
                result[0] = fn(*args, **kwargs)
            except Exception as e:
                error[0] = e
            finally:
                done.set()

        thread = Thread(target=_run, daemon=True)
        thread.start()
        ok = done.wait(timeout=self.max_seconds)
        if not ok:
            if self.raise_on_timeout:
                raise TimeoutError(
                    f"Operation '{self.operation_name}' timed out after {self.max_seconds}s"
                )
            return None
        if error[0] is not None:
            raise error[0]
        return result[0]


class PerformanceHardener:
    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}
        self._timeouts: dict[str, OperationTimeout] = {}
        self._call_count: int = 0
        self._failure_count: int = 0

    def register_breaker(
        self, name: str, config: CircuitBreakerConfig | None = None,
    ) -> CircuitBreaker:
        cfg = config or CircuitBreakerConfig(name=name)
        breaker = CircuitBreaker(cfg)
        self._breakers[name] = breaker
        return breaker

    def register_timeout(self, name: str, max_seconds: float = 10.0) -> OperationTimeout:
        ot = OperationTimeout(operation_name=name, max_seconds=max_seconds)
        self._timeouts[name] = ot
        return ot

    def get_breaker(self, name: str) -> CircuitBreaker | None:
        return self._breakers.get(name)

    def get_timeout(self, name: str) -> OperationTimeout | None:
        return self._timeouts.get(name)

    def protected_call(
        self, breaker_name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any,
    ) -> Any:
        breaker = self._breakers.get(breaker_name)
        if breaker is None:
            return fn(*args, **kwargs)
        try:
            result = breaker.call(fn, *args, **kwargs)
            self._call_count += 1
            return result
        except Exception:
            self._failure_count += 1
            raise

    def timed_call(
        self, timeout_name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any,
    ) -> Any:
        ot = self._timeouts.get(timeout_name)
        if ot is None:
            return fn(*args, **kwargs)
        return ot.execute(fn, *args, **kwargs)

    def reset_all(self) -> None:
        for breaker in self._breakers.values():
            breaker.reset()

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "call_count": self._call_count,
            "failure_count": self._failure_count,
            "breakers": {n: b.stats for n, b in self._breakers.items()},
            "timeouts": list(self._timeouts.keys()),
        }
