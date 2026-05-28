"""Temporary file and artifact cleanup management.

Manages cleanup of temporary files, stale runtime artifacts, and
orphaned data with configurable retention policies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from app.utils.file_utils import cleanup_temp_files
from app.utils.logger import get_logger

logger = get_logger("app.runtime.temp_cleanup")


@dataclass
class CleanupPolicy:
    """Retention policy governing cleanup operations."""

    temp_max_age_hours: int = 24
    archive_temp_max_age_hours: int = 1
    log_max_age_days: int = 30
    backup_max_age_days: int = 90


@dataclass
class CleanupResult:
    """Result of a full cleanup execution."""

    temp_files_removed: int = 0
    archive_temps_removed: int = 0
    old_logs_removed: int = 0
    old_backups_removed: int = 0
    bytes_freed: int = 0
    errors: list[str] = field(default_factory=list)


class TempCleanupManager:
    """Manages cleanup of temporary files, logs, and backups.

    Applies configurable retention policies and delegates low-level
    file operations to utility functions.
    """

    def __init__(
        self,
        data_dirs: dict[str, Path],
        policy: CleanupPolicy | None = None,
    ) -> None:
        self._data_dirs = data_dirs
        self._policy = policy or CleanupPolicy()

    def execute(self) -> CleanupResult:
        """Run all cleanup tasks across configured directories.

        Returns:
            CleanupResult with counts of removed items and freed space.
        """
        result = CleanupResult()

        result.temp_files_removed = self.cleanup_temp_files()
        result.archive_temps_removed = self._cleanup_archive_temps()
        result.old_logs_removed = self.cleanup_old_logs()
        result.old_backups_removed = self.cleanup_old_backups()

        used, _ = self._get_disk_usage()
        result.bytes_freed = used

        logger.info(
            "Cleanup cycle completed",
            extra={
                "temp_removed": result.temp_files_removed,
                "archive_temps_removed": result.archive_temps_removed,
                "logs_removed": result.old_logs_removed,
                "backups_removed": result.old_backups_removed,
                "bytes_freed": result.bytes_freed,
            },
        )
        return result

    def cleanup_temp_files(self) -> int:
        """Clean up temporary .tmp files in the temp directory.

        Returns:
            Number of files removed.
        """
        temp_dir = self._data_dirs.get("temp")
        if not temp_dir or not temp_dir.exists():
            return 0
        try:
            count = cleanup_temp_files(temp_dir, max_age_hours=self._policy.temp_max_age_hours)
            if count > 0:
                logger.info("Temp files cleaned", extra={"count": count})
            return count
        except Exception as exc:
            logger.warning("Temp file cleanup error", extra={"error": str(exc)})
            return 0

    def _cleanup_archive_temps(self) -> int:
        archive_dir = self._data_dirs.get("archives")
        if not archive_dir or not archive_dir.exists():
            return 0
        try:
            count = cleanup_temp_files(
                archive_dir, max_age_hours=self._policy.archive_temp_max_age_hours
            )
            if count > 0:
                logger.info("Archive temps cleaned", extra={"count": count})
            return count
        except Exception as exc:
            logger.warning("Archive temp cleanup error", extra={"error": str(exc)})
            return 0

    def cleanup_old_logs(self) -> int:
        """Remove log files older than the configured retention period.

        Returns:
            Number of log files removed.
        """
        log_dir = self._data_dirs.get("logs")
        if not log_dir or not log_dir.exists():
            return 0
        removed = 0
        cutoff = datetime.now() - timedelta(days=self._policy.log_max_age_days)
        try:
            for log_file in log_dir.glob("*.log*"):
                if log_file.is_file():
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if mtime < cutoff:
                        log_file.unlink()
                        removed += 1
            if removed > 0:
                logger.info("Old logs cleaned", extra={"count": removed})
        except OSError as exc:
            logger.warning("Log cleanup error", extra={"error": str(exc)})
        return removed

    def cleanup_old_backups(self) -> int:
        """Remove backup files older than the configured retention period.

        Returns:
            Number of backup files removed.
        """
        backup_dir = self._data_dirs.get("backups")
        if not backup_dir or not backup_dir.exists():
            return 0
        removed = 0
        cutoff = datetime.now() - timedelta(days=self._policy.backup_max_age_days)
        try:
            for backup_file in backup_dir.iterdir():
                if backup_file.is_file():
                    mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if mtime < cutoff:
                        backup_file.unlink()
                        removed += 1
            if removed > 0:
                logger.info("Old backups cleaned", extra={"count": removed})
        except OSError as exc:
            logger.warning("Backup cleanup error", extra={"error": str(exc)})
        return removed

    def _get_disk_usage(self) -> tuple[int, int]:
        """Get disk usage for the primary data directory.

        Returns:
            Tuple of (used_bytes, free_bytes).
        """
        data_dir = self._data_dirs.get("data") or self._data_dirs.get("temp", Path())
        try:
            from app.utils.file_utils import get_disk_usage

            total, used, free = get_disk_usage(data_dir)
            return used, free
        except Exception:
            return 0, 0
