from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HealthCheckResult:
    healthy: bool
    component: str
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


HealthProbe = Callable[[], HealthCheckResult]


class StartupValidator:
    """Startup health validation harness.

    Runs registered health probes and reports overall status.
    """

    def __init__(self) -> None:
        self._probes: dict[str, HealthProbe] = {}

    def register(self, name: str, probe: HealthProbe) -> None:
        if name in self._probes:
            raise ValueError(f"Probe already registered: {name}")
        self._probes[name] = probe

    def unregister(self, name: str) -> None:
        self._probes.pop(name, None)

    def validate_all(self) -> list[HealthCheckResult]:
        results: list[HealthCheckResult] = []
        for name, probe in self._probes.items():
            try:
                result = probe()
            except Exception as exc:
                result = HealthCheckResult(
                    healthy=False,
                    component=name,
                    message=str(exc),
                )
            results.append(result)
        return results

    @property
    def all_healthy(self) -> bool:
        return all(r.healthy for r in self.validate_all())

    def summary(self) -> dict[str, Any]:
        results = self.validate_all()
        return {
            "all_healthy": all(r.healthy for r in results),
            "total": len(results),
            "passed": sum(1 for r in results if r.healthy),
            "failed": sum(1 for r in results if not r.healthy),
            "results": [
                {
                    "component": r.component,
                    "healthy": r.healthy,
                    "message": r.message,
                    "details": r.details,
                }
                for r in results
            ],
        }
