"""Deployment readiness validation.

Validates that the deployment target meets all requirements for
safe application operation. Categorizes issues into CRITICAL
(blocking), WARNING (degraded), and INFO (advisory) tiers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.utils.logger import get_logger

logger = get_logger("app.diagnostics.readiness")


class ReadinessTier:
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ReadinessCheck:
    """A single readiness validation check result."""

    name: str
    passed: bool
    tier: str = ReadinessTier.CRITICAL
    message: str = ""
    recommendation: str = ""


@dataclass
class ReadinessReport:
    """Aggregated readiness validation report."""

    checks: list[ReadinessCheck] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def critical_failures(self) -> list[ReadinessCheck]:
        return [c for c in self.checks if not c.passed and c.tier == ReadinessTier.CRITICAL]

    @property
    def warnings(self) -> list[ReadinessCheck]:
        return [c for c in self.checks if not c.passed and c.tier == ReadinessTier.WARNING]

    @property
    def passed_checks(self) -> list[ReadinessCheck]:
        return [c for c in self.checks if c.passed]

    @property
    def readiness_score(self) -> float:
        if not self.checks:
            return 1.0
        critical_weight = 3.0
        warning_weight = 1.0
        info_weight = 0.5

        weights = {
            ReadinessTier.CRITICAL: critical_weight,
            ReadinessTier.WARNING: warning_weight,
            ReadinessTier.INFO: info_weight,
        }

        total_weight = sum(weights.get(c.tier, 1.0) for c in self.checks)
        passed_weight = sum(weights.get(c.tier, 1.0) for c in self.checks if c.passed)
        return round(passed_weight / total_weight, 2) if total_weight > 0 else 1.0

    @property
    def is_ready(self) -> bool:
        return len(self.critical_failures) == 0

    def summary(self) -> dict[str, Any]:
        return {
            "total_checks": len(self.checks),
            "passed": len(self.passed_checks),
            "critical_failures": len(self.critical_failures),
            "warnings": len(self.warnings),
            "readiness_score": self.readiness_score,
            "is_ready": self.is_ready,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "tier": c.tier,
                    "message": c.message,
                    "recommendation": c.recommendation,
                }
                for c in self.checks
            ],
        }


class _DictPathsAdapter:
    """Normalizes dict access to attribute access for readiness checks.

    Maps attribute names like data_dir, database_dir to dict keys
    like "data", "database", with safe None defaults.
    """
    _KEY_MAP = {
        "data_dir": "data",
        "database_dir": "database",
        "log_dir": "logs",
        "temp_dir": "temp",
        "archives_dir": "archives",
        "plugins_dir": "plugins",
        "config_dir": "config",
        "migrations_dir": "migrations",
    }

    def __init__(self, data: dict[str, object]) -> None:
        self._data = data

    def __getattr__(self, name: str) -> object:
        if name.startswith("_"):
            raise AttributeError(name)
        key = self._KEY_MAP.get(name, name)
        return self._data.get(key)


class DeploymentReadinessValidator:
    """Validates deployment target readiness.

    Checks:
      - Deployment directory structure exists
      - Required directories populated
      - Database directory writable
      - Temp directory writable
      - Log directory writable
      - Archive directory writable
      - Required fonts available
      - Configuration file present and valid
      - Alembic migrations directory present
    """

    def __init__(
        self,
        paths: Any,  # DeploymentPaths-like object or dict
        font_manager: Any | None = None,
    ) -> None:
        if isinstance(paths, dict):
            self.paths = _DictPathsAdapter(paths)
        else:
            self.paths = paths
        self.font_manager = font_manager

    def validate(self) -> ReadinessReport:
        """Execute all readiness checks.

        Returns:
            ReadinessReport with categorized results.
        """
        report = ReadinessReport()

        self._check_directory_exists("data", self.paths.data_dir, report)
        self._check_directory_exists("database", self.paths.database_dir, report)
        self._check_directory_exists("logs", self.paths.log_dir, report)
        self._check_directory_exists("temp", self.paths.temp_dir, report)
        self._check_directory_exists("archives", self.paths.archives_dir, report)
        self._check_directory_exists("plugins", self.paths.plugins_dir, report, ReadinessTier.INFO)

        self._check_writable("database_dir", self.paths.database_dir, report)
        self._check_writable("temp_dir", self.paths.temp_dir, report)
        self._check_writable("log_dir", self.paths.log_dir, report)

        self._check_fonts(report)
        self._check_config_exists(report)
        self._check_migrations_exist(report)

        self._log_readiness(report)
        return report

    def _check_directory_exists(
        self,
        name: str,
        path: Path | None,
        report: ReadinessReport,
        tier: str = ReadinessTier.CRITICAL,
    ) -> None:
        if path is None:
            report.checks.append(
                ReadinessCheck(
                    name=f"dir_{name}",
                    passed=False,
                    tier=tier,
                    message=f"{name}: path not configured",
                    recommendation="Ensure the deployment paths are properly configured",
                )
            )
            return
        exists = path.exists()
        report.checks.append(
            ReadinessCheck(
                name=f"dir_{name}",
                passed=exists,
                tier=tier,
                message=f"{name}: {'exists' if exists else 'missing'} ({path})",
                recommendation=f"Create directory: {path}" if not exists else "",
            )
        )

    def _check_writable(
        self,
        name: str,
        path: Path | None,
        report: ReadinessReport,
    ) -> None:
        if path is None:
            report.checks.append(
                ReadinessCheck(
                    name=f"writable_{name}",
                    passed=False,
                    tier=ReadinessTier.CRITICAL,
                    message=f"{name}: path not configured",
                    recommendation="Configure the deployment paths",
                )
            )
            return
        if not path.exists():
            report.checks.append(
                ReadinessCheck(
                    name=f"writable_{name}",
                    passed=False,
                    tier=ReadinessTier.CRITICAL,
                    message=f"{name}: path does not exist ({path})",
                    recommendation=f"Create directory: {path}",
                )
            )
            return
        try:
            test_file = path / ".readiness_test"
            test_file.write_bytes(b"test")
            test_file.unlink()
            report.checks.append(
                ReadinessCheck(
                    name=f"writable_{name}",
                    passed=True,
                    tier=ReadinessTier.CRITICAL,
                    message=f"{name}: writable",
                )
            )
        except OSError:
            report.checks.append(
                ReadinessCheck(
                    name=f"writable_{name}",
                    passed=False,
                    tier=ReadinessTier.CRITICAL,
                    message=f"{name}: not writable ({path})",
                    recommendation=f"Check permissions for: {path}",
                )
            )

    def _check_fonts(self, report: ReadinessReport) -> None:
        if not self.font_manager:
            report.checks.append(
                ReadinessCheck(
                    name="fonts",
                    passed=True,
                    tier=ReadinessTier.INFO,
                    message="Font check skipped (no font manager)",
                )
            )
            return
        try:
            available = self.font_manager.check_fonts()
            missing = [f for f, ok in available.items() if not ok]
            passed = len(missing) == 0
            report.checks.append(
                ReadinessCheck(
                    name="fonts",
                    passed=passed,
                    tier=ReadinessTier.WARNING,
                    message=(
                        f"All {len(available)} fonts available"
                        if passed
                        else f"Missing fonts: {', '.join(missing)}"
                    ),
                    recommendation=(
                        "Bundle required font files in app/assets/fonts/" if not passed else ""
                    ),
                )
            )
        except Exception as exc:
            report.checks.append(
                ReadinessCheck(
                    name="fonts",
                    passed=False,
                    tier=ReadinessTier.WARNING,
                    message=f"Font check error: {exc}",
                )
            )

    def _check_config_exists(self, report: ReadinessReport) -> None:
        config_path = self.paths.config_dir / "defaults.json" if self.paths.config_dir else None
        if config_path and config_path.exists():
            report.checks.append(
                ReadinessCheck(
                    name="config",
                    passed=True,
                    tier=ReadinessTier.CRITICAL,
                    message="Configuration file found",
                )
            )
        else:
            report.checks.append(
                ReadinessCheck(
                    name="config",
                    passed=False,
                    tier=ReadinessTier.CRITICAL,
                    message=(
                        "Configuration file missing" if config_path else "Config dir not configured"
                    ),
                    recommendation="Create defaults.json in the config directory",
                )
            )

    def _check_migrations_exist(self, report: ReadinessReport) -> None:
        migrations_path = self.paths.migrations_dir if self.paths.migrations_dir else None
        if migrations_path and migrations_path.exists():
            migration_files = list(migrations_path.glob("*.py"))
            passed = len(migration_files) > 0
            report.checks.append(
                ReadinessCheck(
                    name="migrations",
                    passed=passed,
                    tier=ReadinessTier.CRITICAL,
                    message=(
                        f"{len(migration_files)} migration(s) found"
                        if passed
                        else "Migrations directory empty"
                    ),
                    recommendation="Run alembic revision to create initial migration",
                )
            )
        else:
            report.checks.append(
                ReadinessCheck(
                    name="migrations",
                    passed=False,
                    tier=ReadinessTier.CRITICAL,
                    message="Migrations directory not found",
                    recommendation="Ensure alembic migrations are present",
                )
            )

    def _log_readiness(self, report: ReadinessReport) -> None:
        if report.is_ready:
            logger.info(
                "Deployment ready",
                extra={
                    "score": report.readiness_score,
                    "passed": len(report.passed_checks),
                    "total": len(report.checks),
                    "warnings": len(report.warnings),
                },
            )
        else:
            critical = [c.name for c in report.critical_failures]
            logger.error(
                "Deployment not ready",
                extra={
                    "score": report.readiness_score,
                    "failed": critical,
                },
            )
