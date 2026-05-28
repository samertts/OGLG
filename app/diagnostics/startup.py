"""Startup diagnostics engine.

Orchestrates the full diagnostic sequence at application startup,
executing timed phases and collecting results into a comprehensive
report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.diagnostics.environment import CheckSeverity, EnvironmentCheck, EnvironmentVerifier
from app.diagnostics.readiness import DeploymentReadinessValidator, ReadinessReport
from app.diagnostics.report import EnvironmentDiagnosticsReport
from app.runtime.lifecycle import LifecycleLogger
from app.utils.logger import get_logger

logger = get_logger("app.diagnostics.startup")


@dataclass
class StartupDiagnosticsEngine:
    """Orchestrates startup diagnostics and health validation.

    Runs environment checks, deployment readiness validation,
    generates diagnostic reports, and feeds results into the
    lifecycle logger.
    """

    env_verifier: EnvironmentVerifier | None = None
    readiness_validator: DeploymentReadinessValidator | None = None
    lifecycle: LifecycleLogger | None = None

    def run_diagnostics(self) -> dict[str, Any]:
        """Execute the full diagnostic sequence.

        Runs environment checks, readiness validation, and generates
        a diagnostic report.

        Returns:
            Dictionary with all diagnostic results.
        """
        if self.lifecycle:
            self.lifecycle.begin_step("environment_checks")

        checks = self._run_environment_checks()

        if self.lifecycle:
            self.lifecycle.end_step(
                "environment_checks",
                "ok" if all(c.passed for c in checks) else "warning",
            )
            self.lifecycle.begin_step("readiness_validation")

        readiness = self._run_readiness_validation()

        if self.lifecycle:
            status = "ok" if readiness.is_ready else "error"
            self.lifecycle.end_step("readiness_validation", status)
            self.lifecycle.begin_step("diagnostics_report")

        report = EnvironmentDiagnosticsReport.generate(checks)

        if self.lifecycle:
            self.lifecycle.end_step("diagnostics_report", "ok")

        return {
            "checks": [self._check_to_dict(c) for c in checks],
            "readiness": readiness.summary(),
            "report": report.to_dict(),
            "ready": readiness.is_ready,
        }

    def _run_environment_checks(self) -> list[EnvironmentCheck]:
        if not self.env_verifier:
            return []
        return self.env_verifier.run_all()

    def _run_readiness_validation(self) -> ReadinessReport:
        if not self.readiness_validator:
            return ReadinessReport()
        return self.readiness_validator.validate()

    @staticmethod
    def _check_to_dict(check: EnvironmentCheck) -> dict[str, Any]:
        return {
            "name": check.name,
            "passed": check.passed,
            "severity": check.severity.name,
            "message": check.message,
            "detail": check.detail,
        }
