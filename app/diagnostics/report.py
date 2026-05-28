"""Environment diagnostics report generation.

Aggregates environment check results into a structured diagnostic
report for startup logging and troubleshooting.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from app.deployment.paths import get_deploy_mode as detect_deployment_mode
from app.deployment.platform import detect_platform as get_platform_info
from app.diagnostics.environment import EnvironmentCheck
from app.utils.logger import get_logger

logger = get_logger("app.diagnostics.report")


@dataclass
class EnvironmentDiagnosticsReport:
    """Structured diagnostic report of the runtime environment.

    Generated at startup to record system state for troubleshooting.
    Includes platform info, deployment mode, environment checks,
    and resource measurements.
    """

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    platform: dict[str, Any] = field(default_factory=dict)
    deploy_mode: str = ""
    checks: list[dict[str, Any]] = field(default_factory=list)
    health_score: float = 0.0

    @classmethod
    def generate(
        cls,
        checks: list[EnvironmentCheck],
    ) -> EnvironmentDiagnosticsReport:
        """Generate a diagnostic report from environment checks.

        Args:
            checks: List of EnvironmentCheck results.

        Returns:
            A populated EnvironmentDiagnosticsReport.
        """
        platform_info = get_platform_info()
        deploy_mode = detect_deployment_mode()

        passed = sum(1 for c in checks if c.passed)
        total = len(checks)
        health_score = passed / total if total > 0 else 0.0

        report = cls(
            timestamp=datetime.now().isoformat(),
            platform={
                "system": platform_info.system,
                "version": platform_info.version,
                "build": platform_info.release,
                "arch": platform_info.machine,
            },
            deploy_mode=deploy_mode,
            checks=[cls._check_to_dict(c) for c in checks],
            health_score=round(health_score, 2),
        )

        logger.info(
            "Diagnostics report generated",
            extra={
                "mode": deploy_mode,
                "checks": total,
                "passed": passed,
                "score": report.health_score,
            },
        )

        return report

    @staticmethod
    def _check_to_dict(check: EnvironmentCheck) -> dict[str, Any]:
        return {
            "name": check.name,
            "passed": check.passed,
            "severity": check.severity.name,
            "message": check.message,
            "detail": check.detail,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary(self) -> str:
        """Return a one-line summary of the report."""
        passed = sum(1 for c in self.checks if c["passed"])
        total = len(self.checks)
        return (
            f"[{self.deploy_mode}] Health: {self.health_score:.0%} ({passed}/{total} checks passed)"
        )
