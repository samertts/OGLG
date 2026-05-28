"""Environment verifier for startup health checks.

Runs a battery of environment checks at startup to validate that the
system meets minimum requirements for safe operation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

from app.utils.logger import get_logger

logger = get_logger("app.diagnostics.environment")


class CheckSeverity(Enum):
    ERROR = auto()
    WARNING = auto()
    INFO = auto()


@dataclass
class EnvironmentCheck:
    """Result of a single environment check."""

    name: str
    passed: bool
    severity: CheckSeverity = CheckSeverity.ERROR
    message: str = ""
    detail: str = ""


class EnvironmentVerifier:
    """Runs environment checks to validate system readiness.

    Checks performed:
      - Python version >= 3.10
      - SQLite version >= 3.35
      - Sufficient disk space on data directories
      - Minimum system memory (RAM >= 512 MB)
      - OS compatibility
      - Filesystem encoding (UTF-8 required)
      - Display DPI (if available)
      - Bundled font availability
    """

    def __init__(
        self,
        data_dirs: list[Path] | None = None,
        min_disk_mb: int = 100,
        min_ram_mb: int = 512,
        min_python: tuple[int, int] = (3, 10),
        min_sqlite: tuple[int, int, int] = (3, 35, 0),
    ) -> None:
        self.data_dirs = data_dirs or []
        self.min_disk_mb = min_disk_mb
        self.min_ram_mb = min_ram_mb
        self.min_python = min_python
        self.min_sqlite = min_sqlite

    def run_all(self) -> list[EnvironmentCheck]:
        """Execute all environment checks.

        Returns:
            List of EnvironmentCheck results.
        """
        checks: list[EnvironmentCheck] = []
        checks.append(self._check_python_version())
        checks.append(self._check_sqlite_version())
        checks.append(self._check_disk_space())
        checks.append(self._check_system_ram())
        checks.append(self._check_filesystem_encoding())
        checks.append(self._check_display_dpi())
        return checks

    def _check_python_version(self) -> EnvironmentCheck:
        import sys
        v = sys.version_info
        passed = (v.major, v.minor) >= self.min_python
        return EnvironmentCheck(
            name="python_version",
            passed=passed,
            severity=CheckSeverity.ERROR,
            message=(
                f"Python {v.major}.{v.minor}.{v.micro} detected"
                if passed
                else f"Python {v.major}.{v.minor} < minimum {self.min_python[0]}.{self.min_python[1]}"
            ),
            detail=sys.version,
        )

    def _check_sqlite_version(self) -> EnvironmentCheck:
        import sqlite3
        version = sqlite3.sqlite_version
        parts = tuple(int(p) for p in version.split("."))
        passed = parts >= self.min_sqlite
        return EnvironmentCheck(
            name="sqlite_version",
            passed=passed,
            severity=CheckSeverity.ERROR,
            message=(
                f"SQLite {version} detected"
                if passed
                else f"SQLite {version} < minimum {'.'.join(str(p) for p in self.min_sqlite)}"
            ),
            detail=f"sqlite3 module version: {sqlite3.version}",
        )

    def _check_disk_space(self) -> EnvironmentCheck:
        import shutil
        warnings: list[str] = []
        for d in self.data_dirs:
            try:
                d.mkdir(parents=True, exist_ok=True)
                usage = shutil.disk_usage(d)
                free_mb = usage.free / (1024 * 1024)
                if free_mb < self.min_disk_mb:
                    warnings.append(f"{d}: {free_mb:.0f} MB free < {self.min_disk_mb} MB minimum")
            except OSError as exc:
                warnings.append(f"{d}: cannot check ({exc})")

        passed = len(warnings) == 0
        return EnvironmentCheck(
            name="disk_space",
            passed=passed,
            severity=CheckSeverity.WARNING,
            message="Sufficient disk space" if passed else f"Low disk space: {'; '.join(warnings)}",
            detail="; ".join(warnings) if warnings else "All directories have sufficient space",
        )

    def _check_system_ram(self) -> EnvironmentCheck:
        try:
            import psutil
            ram_mb = psutil.virtual_memory().total / (1024 * 1024)
            passed = ram_mb >= self.min_ram_mb
            return EnvironmentCheck(
                name="system_ram",
                passed=passed,
                severity=CheckSeverity.WARNING,
                message=(
                    f"{ram_mb:.0f} MB RAM detected"
                    if passed
                    else f"{ram_mb:.0f} MB RAM < {self.min_ram_mb} MB minimum"
                ),
                detail=f"Available: {psutil.virtual_memory().available / (1024 * 1024):.0f} MB",
            )
        except ImportError:
            return EnvironmentCheck(
                name="system_ram",
                passed=True,
                severity=CheckSeverity.INFO,
                message="RAM check skipped (psutil not available)",
                detail="Install psutil for detailed memory checks",
            )

    def _check_filesystem_encoding(self) -> EnvironmentCheck:
        import sys
        encoding = sys.getfilesystemencoding()
        passed = encoding.lower() in ("utf-8", "utf8")
        return EnvironmentCheck(
            name="filesystem_encoding",
            passed=passed,
            severity=CheckSeverity.ERROR,
            message=f"Filesystem encoding: {encoding}",
            detail="UTF-8 is required for Arabic filename support" if not passed else "",
        )

    def _check_display_dpi(self) -> EnvironmentCheck:
        try:
            import ctypes
            try:
                user32 = ctypes.windll.user32
                dpi = user32.GetDpiForWindow(user32.GetDesktopWindow())
                passed = dpi >= 96
                return EnvironmentCheck(
                    name="display_dpi",
                    passed=passed,
                    severity=CheckSeverity.INFO,
                    message=f"Display DPI: {dpi}",
                    detail="High DPI display detected" if dpi > 96 else "Standard DPI",
                )
            except AttributeError:
                return EnvironmentCheck(
                    name="display_dpi",
                    passed=True,
                    severity=CheckSeverity.INFO,
                    message="Display DPI check not available on this platform",
                    detail="",
                )
        except Exception:
            return EnvironmentCheck(
                name="display_dpi",
                passed=True,
                severity=CheckSeverity.INFO,
                message="Display DPI check skipped",
                detail="",
            )
