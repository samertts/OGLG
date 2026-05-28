"""Environment validation for pre-startup checks.

Validates Python version, SQLite capabilities, disk space, write
permissions, and platform compatibility before application startup.
"""

from __future__ import annotations

import platform
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("app.diagnostics.environment_validator")


class CheckSeverity(Enum):
    """Severity level for an environment check result."""

    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


@dataclass
class EnvironmentCheck:
    """Result of a single environment validation check."""

    name: str
    passed: bool
    severity: CheckSeverity
    message: str
    detail: str = ""


class EnvironmentValidator:
    """Validates the runtime environment before application startup.

    Runs a battery of checks against the system to ensure minimum
    requirements are met for safe operation, including Python version,
    SQLite capabilities, disk space, write permissions, and platform
    compatibility.

    Args:
        data_dirs: Mapping of logical directory names to their paths.
    """

    def __init__(self, data_dirs: dict[str, Path] | None = None) -> None:
        self.data_dirs = data_dirs or {}

    def run_all(self) -> list[EnvironmentCheck]:
        """Execute all environment validation checks.

        Returns:
            A list of EnvironmentCheck results for every check.
        """
        checks: list[EnvironmentCheck] = []
        checks.append(self.check_python_version())
        checks.append(self.check_sqlite_version())
        checks.append(self.check_disk_space())
        checks.append(self.check_write_permissions())
        checks.append(self.check_platform_compatibility())
        checks.append(self.check_sqlite_wal_mode())
        return checks

    def check_python_version(self) -> EnvironmentCheck:
        """Verify Python runtime is at least 3.12.

        Returns:
            EnvironmentCheck indicating whether Python >= 3.12.
        """
        v = sys.version_info
        passed = (v.major, v.minor) >= (3, 12)
        return EnvironmentCheck(
            name="python_version",
            passed=passed,
            severity=CheckSeverity.CRITICAL,
            message=(
                f"Python {v.major}.{v.minor}.{v.micro} detected"
                if passed
                else f"Python {v.major}.{v.minor} < minimum 3.12"
            ),
            detail=sys.version,
        )

    def check_sqlite_version(self) -> EnvironmentCheck:
        """Verify SQLite version is at least 3.35 (WAL mode support).

        Returns:
            EnvironmentCheck indicating whether SQLite >= 3.35.
        """
        version = sqlite3.sqlite_version
        parts = tuple(int(p) for p in version.split("."))
        passed = parts >= (3, 35, 0)
        return EnvironmentCheck(
            name="sqlite_version",
            passed=passed,
            severity=CheckSeverity.CRITICAL,
            message=(
                f"SQLite {version} detected (WAL supported)"
                if passed
                else f"SQLite {version} < minimum 3.35 (WAL not supported)"
            ),
            detail=f"sqlite3 module version: {sqlite3.version}",
        )

    def check_disk_space(self) -> EnvironmentCheck:
        """Verify at least 500 MB free on each data directory.

        Returns:
            EnvironmentCheck with warnings if space is low.
        """
        warnings: list[str] = []
        for name, path in self.data_dirs.items():
            try:
                path.mkdir(parents=True, exist_ok=True)
                usage = shutil.disk_usage(path)
                free_mb = usage.free / (1024 * 1024)
                if free_mb < 500:
                    warnings.append(f"{name} ({path}): {free_mb:.0f} MB free < 500 MB minimum")
            except OSError as exc:
                warnings.append(f"{name} ({path}): cannot check ({exc})")

        passed = len(warnings) == 0
        return EnvironmentCheck(
            name="disk_space",
            passed=passed,
            severity=CheckSeverity.WARNING,
            message=(
                "Sufficient disk space (>= 500 MB)"
                if passed
                else f"Low disk space: {'; '.join(warnings)}"
            ),
            detail="; ".join(warnings)
            if warnings
            else "All data directories have sufficient space",
        )

    def check_write_permissions(self) -> EnvironmentCheck:
        """Verify all data directories are writable.

        Attempts to create and remove a test file in each directory.

        Returns:
            EnvironmentCheck indicating write permission status.
        """
        failures: list[str] = []
        for name, path in self.data_dirs.items():
            try:
                path.mkdir(parents=True, exist_ok=True)
                test_file = path / ".env_validator_write_test"
                test_file.write_bytes(b"test")
                test_file.unlink()
            except OSError as exc:
                failures.append(f"{name} ({path}): {exc}")

        passed = len(failures) == 0
        return EnvironmentCheck(
            name="write_permissions",
            passed=passed,
            severity=CheckSeverity.CRITICAL,
            message=(
                "All data directories writable"
                if passed
                else f"Write failures: {'; '.join(failures)}"
            ),
            detail="; ".join(failures) if failures else "Write test passed for all directories",
        )

    def check_platform_compatibility(self) -> EnvironmentCheck:
        """Check if the current platform is fully supported.

        Issues a warning on non-Windows platforms since the system is
        designed for Windows-based government deployments.

        Returns:
            EnvironmentCheck with platform compatibility information.
        """
        system = platform.system()
        passed = system == "Windows"
        return EnvironmentCheck(
            name="platform_compatibility",
            passed=passed,
            severity=CheckSeverity.WARNING,
            message=(
                f"Platform: {system} (fully supported)"
                if passed
                else f"Platform: {system} (limited support — Windows recommended for production)"
            ),
            detail=f"Platform details: {platform.platform()}",
        )

    def check_sqlite_wal_mode(self) -> EnvironmentCheck:
        """Verify SQLite Write-Ahead Logging (WAL) mode is available.

        Opens an in-memory database and attempts to switch to WAL mode.

        Returns:
            EnvironmentCheck indicating WAL mode availability.
        """
        try:
            conn = sqlite3.connect(":memory:")
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.close()
            return EnvironmentCheck(
                name="sqlite_wal_mode",
                passed=True,
                severity=CheckSeverity.CRITICAL,
                message="SQLite WAL mode is available",
                detail="Write-Ahead Logging is supported by the SQLite build",
            )
        except sqlite3.OperationalError as exc:
            return EnvironmentCheck(
                name="sqlite_wal_mode",
                passed=False,
                severity=CheckSeverity.CRITICAL,
                message="SQLite WAL mode is NOT available",
                detail=str(exc),
            )

    def summarize(self, checks: list[EnvironmentCheck]) -> dict:
        """Count passed, failed, warning, and error checks.

        Args:
            checks: List of EnvironmentCheck results to summarize.

        Returns:
            Dictionary with total, passed, failed, warnings, errors,
            and all_passed keys.
        """
        total = len(checks)
        passed = sum(1 for c in checks if c.passed)
        failed = total - passed
        warnings = sum(1 for c in checks if c.severity == CheckSeverity.WARNING and not c.passed)
        errors = sum(
            1
            for c in checks
            if c.severity in (CheckSeverity.ERROR, CheckSeverity.CRITICAL) and not c.passed
        )
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "errors": errors,
            "all_passed": passed == total,
        }
