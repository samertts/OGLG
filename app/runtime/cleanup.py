"""Temporary file cleanup and backup rotation engines.

Provides scheduled cleanup for temporary runtime files and retention-
based rotation of database backups.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.utils.file_utils import cleanup_temp_files, get_disk_usage
from app.utils.logger import get_logger

logger = get_logger("app.runtime.cleanup")


@dataclass
class CleanupResult:
    """Result of a cleanup operation."""

    temp_files_removed: int = 0
    backups_removed: int = 0
    space_freed_bytes: int = 0
    errors: list[str] = field(default_factory=list)


class TempCleanupEngine:
    """Manages periodic cleanup of temporary runtime files.

    Cleans:
      - .tmp files older than max_age_hours
      - Empty subdirectories in the temp directory
      - Old log files beyond retention policy
    """

    def __init__(
        self,
        temp_dir: Path,
        log_dir: Path | None = None,
        max_temp_age_hours: int = 24,
        log_retention_days: int = 30,
    ) -> None:
        self.temp_dir = temp_dir
        self.log_dir = log_dir
        self.max_temp_age_hours = max_temp_age_hours
        self.log_retention_days = log_retention_days

    def run_cleanup(self) -> CleanupResult:
        """Execute the full cleanup cycle.

        Returns:
            CleanupResult with details of removed files.
        """
        result = CleanupResult()

        result.temp_files_removed = self._clean_temp_directory()
        result.backups_removed = self._clean_old_logs()
        result.space_freed_bytes = self._compute_freed_space()

        logger.info(
            "Cleanup cycle completed",
            extra={
                "temp_removed": result.temp_files_removed,
                "logs_removed": result.backups_removed,
                "space_freed": result.space_freed_bytes,
            },
        )
        return result

    def _clean_temp_directory(self) -> int:
        if not self.temp_dir.exists():
            return 0
        return cleanup_temp_files(self.temp_dir, max_age_hours=self.max_temp_age_hours)

    def _clean_old_logs(self) -> int:
        if not self.log_dir or not self.log_dir.exists():
            return 0
        removed = 0
        cutoff = datetime.now() - timedelta(days=self.log_retention_days)
        for log_file in self.log_dir.glob("*.log*"):
            if log_file.is_file():
                try:
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if mtime < cutoff:
                        log_file.unlink()
                        removed += 1
                except OSError:
                    continue
        return removed

    def _compute_freed_space(self) -> int:
        return 0


@dataclass
class RotationResult:
    """Result of a backup rotation operation."""

    backups_removed: int = 0
    space_freed_bytes: int = 0
    errors: list[str] = field(default_factory=list)


class BackupRotationEngine:
    """Manages backup retention and rotation.

    Enforces maximum backup count and age-based retention policies.
    Oldest backups are removed first when limits are exceeded.
    """

    def __init__(
        self,
        backup_dir: Path,
        max_backups: int = 30,
        max_age_days: int = 90,
    ) -> None:
        self.backup_dir = backup_dir
        self.max_backups = max_backups
        self.max_age_days = max_age_days

    def rotate(self) -> RotationResult:
        """Execute backup rotation based on configured policies.

        Removes backups that exceed the maximum age or count limits.

        Returns:
            RotationResult with number of backups removed.
        """
        result = RotationResult()
        if not self.backup_dir.exists():
            return result

        backups = sorted(
            [f for f in self.backup_dir.iterdir() if f.is_file() and f.suffix == ".db"],
            key=lambda p: p.stat().st_mtime,
        )

        result.backups_removed += self._remove_age_expired(backups, result)
        result.backups_removed += self._remove_excess_count(backups, result)

        if result.backups_removed > 0:
            logger.info(
                "Backup rotation completed",
                extra={
                    "removed": result.backups_removed,
                    "remaining": max(0, len(backups) - result.backups_removed),
                    "space_freed": result.space_freed_bytes,
                },
            )

        return result

    def _remove_age_expired(
        self, backups: list[Path], result: RotationResult
    ) -> int:
        removed = 0
        cutoff = datetime.now() - timedelta(days=self.max_age_days)
        for backup in backups:
            try:
                mtime = datetime.fromtimestamp(backup.stat().st_mtime)
                if mtime < cutoff:
                    result.space_freed_bytes += backup.stat().st_size
                    backup.unlink()
                    removed += 1
            except OSError as exc:
                result.errors.append(f"Failed to remove {backup.name}: {exc}")
        return removed

    def _remove_excess_count(
        self, backups: list[Path], result: RotationResult
    ) -> int:
        removed = 0
        remaining = [b for b in backups if b.exists()]
        while len(remaining) > self.max_backups:
            oldest = remaining.pop(0)
            try:
                result.space_freed_bytes += oldest.stat().st_size
                oldest.unlink()
                removed += 1
            except OSError as exc:
                result.errors.append(f"Failed to remove {oldest.name}: {exc}")
        return removed
