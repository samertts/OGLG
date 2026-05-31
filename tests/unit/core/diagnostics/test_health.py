from __future__ import annotations

import pytest

from app.core.diagnostics.health import HealthCheckResult, StartupValidator


def test_startup_validator_all_healthy() -> None:
    v = StartupValidator()
    v.register("db", lambda: HealthCheckResult(healthy=True, component="db"))
    v.register("fs", lambda: HealthCheckResult(healthy=True, component="fs"))
    assert v.all_healthy
    summary = v.summary()
    assert summary["passed"] == 2
    assert summary["failed"] == 0


def test_startup_validator_failure() -> None:
    v = StartupValidator()
    v.register("db", lambda: HealthCheckResult(healthy=True, component="db"))
    v.register("fs", lambda: HealthCheckResult(healthy=False, component="fs", message="disk full"))
    assert not v.all_healthy
    summary = v.summary()
    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert summary["results"][1]["message"] == "disk full"


def test_startup_validator_exception_safe() -> None:
    v = StartupValidator()

    def broken() -> HealthCheckResult:
        raise RuntimeError("kaboom")

    v.register("broken", broken)
    results = v.validate_all()
    assert len(results) == 1
    assert not results[0].healthy
    assert "kaboom" in results[0].message


def test_startup_validator_register_duplicate() -> None:
    v = StartupValidator()
    v.register("x", lambda: HealthCheckResult(healthy=True, component="x"))
    with pytest.raises(ValueError, match="already registered"):
        v.register("x", lambda: HealthCheckResult(healthy=True, component="x"))


def test_startup_validator_unregister() -> None:
    v = StartupValidator()
    v.register("x", lambda: HealthCheckResult(healthy=True, component="x"))
    v.unregister("x")
    assert v.all_healthy
