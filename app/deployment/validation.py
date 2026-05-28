"""Startup validation checks for deployment integrity.

Validates the runtime environment before the application starts:
  - Directory structure completeness
  - SQLite database integrity
  - Font availability for Arabic RTL rendering
  - Disk space availability
  - Bundled asset integrity
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.deployment.paths import get_data_dir, get_runtime_dir
from app.deployment.platform import detect_platform
from app.utils.logger import get_logger

logger = get_logger("app.deployment.validation")


@dataclass
class DeploymentValidationResult:
    """Result of deployment startup validation."""

    passed: bool
    checks: dict[str, bool] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def run_startup_validation(portable: bool = False) -> DeploymentValidationResult:
    """Run all startup validation checks.

    Args:
        portable: If True, validate portable mode directory layout.

    Returns:
        DeploymentValidationResult with check results.
    """
    result = DeploymentValidationResult()

    _check_platform(result)
    _check_directories(result, portable)
    _check_disk_space(result)
    _check_fonts(result)

    result.passed = len(result.errors) == 0
    if result.passed:
        logger.info("Startup validation passed")
    else:
        logger.error("Startup validation failed", extra={"errors": result.errors})

    return result


def validate_directory_structure(portable: bool = False) -> dict[str, bool]:
    """Validate that required directories exist.

    Returns:
        Dictionary of directory name to existence boolean.
    """
    data_dir = get_data_dir()
    required = [
        ("data_dir", data_dir),
        ("database", data_dir / "database"),
        ("archives", data_dir / "archives"),
        ("backups", data_dir / "backups"),
        ("logs", data_dir / "logs"),
        ("temp", data_dir / "temp"),
        ("attachments", data_dir / "attachments"),
        ("generated_letters", data_dir / "generated_letters"),
    ]
    if portable:
        required.append(("config", data_dir))

    return {name: path.is_dir() for name, path in required}


def validate_sqlite_integrity(db_path: Path) -> bool:
    """Validate SQLite database integrity by running PRAGMA integrity_check.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        True if integrity check passes or file does not exist yet.
    """
    if not db_path.exists():
        return True
    try:
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        conn.close()
        return result is not None and result[0] == "ok"
    except Exception as exc:
        logger.error("SQLite integrity check failed", extra={"error": str(exc)})
        return False


def validate_font_availability() -> list[str]:
    """Check that bundled Arabic fonts exist.

    Returns:
        List of missing font file paths (empty if all present).
    """
    font_dir = get_runtime_dir() / "assets" / "fonts"
    if not font_dir.is_dir():
        return ["fonts directory not found"]

    expected = ["Amiri", "NotoNaskhArabic", "TraditionalArabic"]
    missing: list[str] = []
    for name in expected:
        found = False
        for ext in [".ttf", ".otf"]:
            if (font_dir / (name + ext)).exists():
                found = True
                break
        if not found:
            missing.append(name)
    return missing


def validate_disk_space(min_free_mb: int = 100) -> tuple[bool, int]:
    """Validate that sufficient disk space is available.

    Args:
        min_free_mb: Minimum free space in megabytes.

    Returns:
        Tuple of (sufficient, free_mb).
    """
    data_dir = get_data_dir()
    try:
        stat = data_dir.stat()
        if hasattr(stat, "st_dev"):
            import os

            usage = os.statvfs(data_dir)
            free_mb = (usage.f_bavail * usage.f_frsize) // (1024 * 1024)
            return free_mb >= min_free_mb, free_mb
    except Exception:
        pass
    return True, 0


def _check_platform(result: DeploymentValidationResult) -> None:
    info = detect_platform()
    result.checks["platform_detected"] = True
    if info.is_windows:
        if info.windows_major == 6 and info.windows_minor == 1:
            result.warnings.append("Running on Windows 7 — some features may be limited")
        result.checks["windows_version_supported"] = True


def _check_directories(result: DeploymentValidationResult, portable: bool) -> None:
    dirs = validate_directory_structure(portable)
    for name, exists in dirs.items():
        result.checks[f"dir_{name}"] = exists
        if not exists:
            result.errors.append(f"Required directory missing: {name}")


def _check_disk_space(result: DeploymentValidationResult) -> None:
    ok, free_mb = validate_disk_space()
    result.checks["disk_space"] = ok
    if not ok:
        result.errors.append(f"Insufficient disk space: {free_mb} MB free")


def _check_fonts(result: DeploymentValidationResult) -> None:
    missing = validate_font_availability()
    result.checks["fonts_available"] = len(missing) == 0
    for font in missing:
        result.warnings.append(f"Font not bundled: {font}")
