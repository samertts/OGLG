"""Pre-flight startup validation checks.

Runs before the main startup sequence to verify the system can
initialize safely.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("app.diagnostics.startup_checks")


@dataclass
class StartupCheck:
    """Result of a single pre-flight startup check."""

    name: str
    passed: bool
    critical: bool
    message: str
    detail: str = ""


@dataclass
class StartupCheckResult:
    """Aggregated result of all pre-flight startup checks."""

    all_passed: bool
    checks: list[StartupCheck] = field(default_factory=list)
    critical_failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class StartupChecks:
    """Pre-flight startup validation checks.

    Verifies data directories exist, database path is writable,
    migrations are available, assets and config are present, fonts
    are available, and the temp directory is usable.

    Args:
        data_dirs: Mapping of logical directory names to their paths.
        db_path: Optional path to the SQLite database file.
    """

    def __init__(self, data_dirs: dict[str, Path], db_path: Path | None = None) -> None:
        self.data_dirs = data_dirs
        self.db_path = db_path

    def run_all(self) -> StartupCheckResult:
        """Execute all startup checks and return the aggregated result.

        Returns:
            StartupCheckResult with all individual check results.
        """
        checks: list[StartupCheck] = []
        checks.append(self.check_data_dirs_exist())
        checks.append(self.check_database_path_writable())
        checks.append(self.check_migrations_available())
        checks.append(self.check_assets_exist())
        checks.append(self.check_config_exists())
        checks.append(self.check_fonts_available())
        checks.append(self.check_temp_is_writable())

        critical_failures = [c.name for c in checks if not c.passed and c.critical]
        warnings = [c.name for c in checks if not c.passed and not c.critical]
        all_passed = len(critical_failures) == 0

        result = StartupCheckResult(
            all_passed=all_passed,
            checks=checks,
            critical_failures=critical_failures,
            warnings=warnings,
        )

        logger.info(
            "Startup checks completed",
            extra={
                "all_passed": all_passed,
                "total": len(checks),
                "critical_failures": len(critical_failures),
                "warnings": len(warnings),
            },
        )

        return result

    def check_data_dirs_exist(self) -> StartupCheck:
        """Verify all configured data directories exist on disk.

        Returns:
            StartupCheck indicating whether all directories are present.
        """
        missing: list[str] = []
        for name, path in self.data_dirs.items():
            if not path.exists():
                missing.append(f"{name} ({path})")

        passed = len(missing) == 0
        return StartupCheck(
            name="data_dirs_exist",
            passed=passed,
            critical=True,
            message="All data directories exist"
            if passed
            else f"Missing data directories: {'; '.join(missing)}",
            detail="; ".join(missing) if missing else "All configured data directories are present",
        )

    def check_database_path_writable(self) -> StartupCheck:
        """Verify the database parent directory is writable.

        Returns:
            StartupCheck indicating database path writability.
        """
        if self.db_path is None:
            return StartupCheck(
                name="database_path_writable",
                passed=False,
                critical=True,
                message="Database path not configured",
                detail="db_path was not provided to startup checks",
            )

        parent = self.db_path.parent
        try:
            parent.mkdir(parents=True, exist_ok=True)
            test_file = parent / ".startup_db_write_test"
            test_file.write_bytes(b"test")
            test_file.unlink()
            return StartupCheck(
                name="database_path_writable",
                passed=True,
                critical=True,
                message=f"Database path is writable ({parent})",
            )
        except OSError as exc:
            return StartupCheck(
                name="database_path_writable",
                passed=False,
                critical=True,
                message=f"Database path not writable: {exc}",
                detail=f"Parent directory: {parent}",
            )

    def check_migrations_available(self) -> StartupCheck:
        """Verify alembic.ini exists in the current working directory.

        Returns:
            StartupCheck indicating migration availability.
        """
        alembic_ini = Path(os.getcwd()) / "alembic.ini"
        passed = alembic_ini.exists()
        return StartupCheck(
            name="migrations_available",
            passed=passed,
            critical=True,
            message="Alembic migrations available" if passed else "alembic.ini not found",
            detail=str(alembic_ini)
            if passed
            else "Run 'alembic init alembic' to create migrations",
        )

    def check_assets_exist(self) -> StartupCheck:
        """Verify the app/assets directory exists.

        Returns:
            StartupCheck indicating asset directory presence.
        """
        assets_dir = Path("app/assets")
        passed = assets_dir.exists()
        return StartupCheck(
            name="assets_exist",
            passed=passed,
            critical=False,
            message="Assets directory found" if passed else "app/assets directory not found",
            detail=str(assets_dir)
            if passed
            else "Create the app/assets directory with required resources",
        )

    def check_config_exists(self) -> StartupCheck:
        """Verify the defaults.json configuration file exists.

        Returns:
            StartupCheck indicating configuration file presence.
        """
        config_path = Path("app/config/defaults.json")
        passed = config_path.exists()
        return StartupCheck(
            name="config_exists",
            passed=passed,
            critical=True,
            message="Configuration file found" if passed else "defaults.json not found",
            detail=str(config_path)
            if passed
            else "Create app/config/defaults.json with default configuration",
        )

    def check_fonts_available(self) -> StartupCheck:
        """Verify the fonts directory under app/assets exists.

        Returns:
            StartupCheck indicating font directory presence.
        """
        fonts_dir = Path("app/assets/fonts")
        passed = fonts_dir.exists()
        return StartupCheck(
            name="fonts_available",
            passed=passed,
            critical=False,
            message="Fonts directory found" if passed else "Fonts directory not found",
            detail=str(fonts_dir)
            if passed
            else "Create app/assets/fonts/ with required font files",
        )

    def check_temp_is_writable(self) -> StartupCheck:
        """Verify the temp directory exists and is writable.

        Falls back to a 'temp' directory relative to cwd if not
        configured in data_dirs.

        Returns:
            StartupCheck indicating temp directory writability.
        """
        temp_dir = self.data_dirs.get("temp", Path("temp"))
        try:
            temp_dir.mkdir(parents=True, exist_ok=True)
            test_file = temp_dir / ".startup_temp_write_test"
            test_file.write_bytes(b"test")
            test_file.unlink()
            return StartupCheck(
                name="temp_is_writable",
                passed=True,
                critical=True,
                message=f"Temp directory is writable ({temp_dir})",
            )
        except OSError as exc:
            return StartupCheck(
                name="temp_is_writable",
                passed=False,
                critical=True,
                message=f"Temp directory not writable: {exc}",
                detail=str(temp_dir),
            )
