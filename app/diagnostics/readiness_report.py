"""Deployment readiness reporting.

Generates comprehensive readiness reports from environment validation,
startup checks, and dependency verification results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto

from app.diagnostics.startup_checks import StartupCheckResult
from app.utils.logger import get_logger

logger = get_logger("app.diagnostics.readiness_report")


class ReadinessLevel(Enum):
    """Overall readiness level of the application for operation."""

    READY = auto()
    DEGRADED = auto()
    NOT_READY = auto()
    UNKNOWN = auto()


@dataclass
class ReadinessReport:
    """Comprehensive readiness report generated from all diagnostic sources."""

    level: ReadinessLevel
    overall_score: float
    checks_passed: int
    checks_total: int
    critical_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0


class ReadinessReportGenerator:
    """Generates readiness reports from environment, startup, and dependency checks.

    Aggregates results from multiple diagnostic sources into a single
    readiness report with a computed score and level classification.
    """

    def __init__(self) -> None:
        pass

    def generate(
        self,
        env_checks: list,
        startup_result: StartupCheckResult,
        dep_checks: list,
    ) -> ReadinessReport:
        """Generate a comprehensive readiness report from all diagnostic sources.

        Args:
            env_checks: List of environment check results.
            startup_result: Aggregated startup check result.
            dep_checks: List of dependency check results.

        Returns:
            A populated ReadinessReport with score, level, and categorized issues.
        """
        start = datetime.now()

        critical_issues: list[str] = []
        warnings: list[str] = []
        info: list[str] = []
        passed = 0
        total = 0

        for check in env_checks:
            total += 1
            if check.passed:
                passed += 1
            else:
                severity = getattr(check, "severity", None)
                if severity is not None and severity.name in ("CRITICAL", "ERROR"):
                    critical_issues.append(f"[ENV] {check.name}: {check.message}")
                else:
                    warnings.append(f"[ENV] {check.name}: {check.message}")

        for check in startup_result.checks:
            total += 1
            if check.passed:
                passed += 1
            elif check.critical:
                critical_issues.append(f"[STARTUP] {check.name}: {check.message}")
            else:
                warnings.append(f"[STARTUP] {check.name}: {check.message}")

        for check in dep_checks:
            total += 1
            status_name = check.status.name if hasattr(check.status, "name") else str(check.status)
            if status_name == "AVAILABLE":
                passed += 1
            else:
                critical_issues.append(f"[DEP] {check.name}: {check.message}")

        score = self._calculate_score(passed, total)
        level = self._determine_level(score, critical_issues)

        if level == ReadinessLevel.READY:
            info.append("All checks passed — system is ready")

        duration = (datetime.now() - start).total_seconds() * 1000

        report = ReadinessReport(
            level=level,
            overall_score=score,
            checks_passed=passed,
            checks_total=total,
            critical_issues=critical_issues,
            warnings=warnings,
            info=info,
            timestamp=datetime.now(),
            duration_ms=round(duration, 2),
        )

        logger.info(
            "Readiness report generated",
            extra={
                "level": level.name,
                "score": score,
                "passed": passed,
                "total": total,
                "duration_ms": report.duration_ms,
            },
        )

        return report

    def _calculate_score(self, passed: int, total: int) -> float:
        """Compute the readiness score as a float between 0.0 and 1.0.

        Args:
            passed: Number of checks that passed.
            total: Total number of checks.

        Returns:
            Score rounded to two decimal places.
        """
        if total == 0:
            return 0.0
        return round(passed / total, 2)

    def _determine_level(self, score: float, critical_failures: list[str]) -> ReadinessLevel:
        """Determine the readiness level based on score and critical failures.

        Args:
            score: The computed readiness score.
            critical_failures: List of critical failure descriptions.

        Returns:
            The appropriate ReadinessLevel.
        """
        if critical_failures:
            return ReadinessLevel.NOT_READY
        if score >= 0.9:
            return ReadinessLevel.READY
        if score >= 0.5:
            return ReadinessLevel.DEGRADED
        if score > 0:
            return ReadinessLevel.NOT_READY
        return ReadinessLevel.UNKNOWN

    def to_dict(self, report: ReadinessReport) -> dict:
        """Serialize a ReadinessReport to a plain dictionary.

        Args:
            report: The ReadinessReport to serialize.

        Returns:
            Dictionary representation of the report.
        """
        return {
            "level": report.level.name,
            "overall_score": report.overall_score,
            "checks_passed": report.checks_passed,
            "checks_total": report.checks_total,
            "critical_issues": report.critical_issues,
            "warnings": report.warnings,
            "info": report.info,
            "timestamp": report.timestamp.isoformat(),
            "duration_ms": report.duration_ms,
        }

    def print_summary(self, report: ReadinessReport) -> None:
        """Print a human-readable summary line to stdout.

        Args:
            report: The ReadinessReport to summarize.
        """
        level_name = report.level.name
        score_pct = f"{report.overall_score:.0%}"
        summary = (
            f"[Readiness: {level_name}] Score: {score_pct} | "
            f"{report.checks_passed}/{report.checks_total} checks passed | "
            f"{len(report.critical_issues)} critical, {len(report.warnings)} warnings | "
            f"{report.duration_ms:.0f}ms"
        )
        print(summary)
        logger.info("Readiness summary printed", extra={"summary": summary})
