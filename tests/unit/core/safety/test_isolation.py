from __future__ import annotations

import pytest

from app.core.safety.isolation import (
    MemoryPressureGuard,
    SubsystemIsolation,
    subsystem_boundary,
)


def test_subsystem_isolation_basic() -> None:
    iso = SubsystemIsolation("test")
    result = iso.execute(lambda: 42)
    assert result == 42
    assert iso.total_calls == 1
    assert iso.total_errors == 0


def test_subsystem_isolation_error_tracking() -> None:
    iso = SubsystemIsolation("test")

    def fail() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        iso.execute(fail)
    assert iso.total_calls == 1
    assert iso.total_errors == 1


def test_subsystem_isolation_error_rate() -> None:
    iso = SubsystemIsolation("test")
    assert iso.error_rate == 0.0
    iso.execute(lambda: 1)
    with pytest.raises(ValueError):
        iso.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
    assert iso.error_rate == 0.5


def test_subsystem_isolation_state() -> None:
    iso = SubsystemIsolation("worker")
    iso.execute(lambda: 1)
    state = iso.state()
    assert state["name"] == "worker"
    assert state["total_calls"] == 1


def test_subsystem_boundary_decorator() -> None:
    @subsystem_boundary("math")
    def add(a: int, b: int) -> int:
        return a + b

    assert add(1, 2) == 3


def test_memory_pressure_guard_invalid() -> None:
    with pytest.raises(ValueError):
        MemoryPressureGuard(warning_mb=800, critical_mb=500)


def test_memory_pressure_guard_start_stop() -> None:
    guard = MemoryPressureGuard(warning_mb=500, critical_mb=800)
    assert not guard.state()["running"]
    guard.start()
    assert guard.state()["running"]
    guard.stop()
    assert not guard.state()["running"]
