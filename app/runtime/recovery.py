"""Crash recovery bootstrap.

Detects unclean shutdowns, validates database integrity, cleans up
stale temporary files, and restores the application to a safe state
before normal startup proceeds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from app.deployment.validation import validate_sqlite_integrity
from app.utils.file_utils import cleanup_temp_files
from app.utils.logger import get_logger

logger = get_logger("app.runtime.recovery")


@dataclass
class RecoveryResult:
    """Result of a crash recovery attempt."""

    recovered: bool
    integrity_ok: bool
    temp_files_cleaned: int = 0
    stale_lock_cleared: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class CrashRecoveryBootstrap:
    """Detects and recovers from unclean application shutdowns.

    Checks:
      - Stale lock files from previous runs
      - SQLite database integrity
      - Stale temporary files exceeding age threshold
      - Incomplete archive operations
    """

    def __init__(
        self,
        data_dirs: dict[str, Path],
        db_path: Path | None = None,
        lock_timeout_minutes: int = 30,
        temp_cleanup_hours: int = 24,
    ) -> None:
        self.data_dirs = data_dirs
        self.db_path = db_path or (data_dirs.get("database", Path()) / "correspondence.db")
        self.lock_timeout_minutes = lock_timeout_minutes
        self.temp_cleanup_hours = temp_cleanup_hours

    def run_recovery(self) -> RecoveryResult:
        """Execute the full crash recovery sequence.

        Returns:
            RecoveryResult with details of what was recovered.
        """
        result = RecoveryResult(recovered=False, integrity_ok=False)

        self._check_stale_locks(result)
        self._check_database_integrity(result)
        self._cleanup_temp_files(result)
        self._clear_stale_archives(result)

        result.recovered = (
            result.integrity_ok or result.temp_files_cleaned > 0 or result.stale_lock_cleared
        )

        if result.recovered:
            logger.info(
                "Crash recovery completed",
                extra={
                    "integrity_ok": result.integrity_ok,
                    "temp_cleaned": result.temp_files_cleaned,
                    "lock_cleared": result.stale_lock_cleared,
                },
            )
        else:
            logger.info("No recovery actions needed")

        return result

    def _check_stale_locks(self, result: RecoveryResult) -> None:
        lock_path = self.data_dirs.get("temp", Path()) / "app.lock"
        if not lock_path.exists():
            return

        try:
            content = lock_path.read_text(encoding="utf-8").strip()
            if content:
                try:
                    lock_time = datetime.fromisoformat(content)
                    age = datetime.now() - lock_time
                    if age > timedelta(minutes=self.lock_timeout_minutes):
                        lock_path.unlink()
                        result.stale_lock_cleared = True
                        result.warnings.append(
                            f"Stale lock file removed (age: {age.total_seconds():.0f}s)"
                        )
                    else:
                        result.warnings.append(
                            f"Lock file still valid (age: {age.total_seconds():.0f}s)"
                        )
                except ValueError:
                    lock_path.unlink()
                    result.stale_lock_cleared = True
                    result.warnings.append("Unparseable lock file removed")
        except OSError as exc:
            result.errors.append(f"Failed to check lock file: {exc}")

    def _check_database_integrity(self, result: RecoveryResult) -> None:
        if not self.db_path.exists():
            result.integrity_ok = True
            return

        try:
            ok = validate_sqlite_integrity(self.db_path)
            result.integrity_ok = ok
            if not ok:
                result.errors.append("Database integrity check failed")
                self._attempt_repair(result)
        except Exception as exc:
            result.errors.append(f"Database check error: {exc}")
            result.integrity_ok = False

    def _attempt_repair(self, result: RecoveryResult) -> None:
        """Attempt VACUUM-based repair on corrupted database."""
        try:
            import sqlite3

            conn = sqlite3.connect(str(self.db_path))
            conn.execute("VACUUM")
            conn.close()
            ok = validate_sqlite_integrity(self.db_path)
            if ok:
                result.integrity_ok = True
                result.warnings.append("Database repaired via VACUUM")
            else:
                result.errors.append("VACUUM repair failed")
        except Exception as exc:
            result.errors.append(f"Repair attempt failed: {exc}")

    def _cleanup_temp_files(self, result: RecoveryResult) -> None:
        temp_dir = self.data_dirs.get("temp")
        if not temp_dir or not temp_dir.exists():
            return
        try:
            count = cleanup_temp_files(temp_dir, max_age_hours=self.temp_cleanup_hours)
            result.temp_files_cleaned = count
            if count > 0:
                logger.info("Temporary files cleaned", extra={"count": count})
        except Exception as exc:
            result.warnings.append(f"Temp cleanup error: {exc}")

    def _clear_stale_archives(self, result: RecoveryResult) -> None:
        """Clean up .tmp files in the archives directory from interrupted operations."""
        archive_dir = self.data_dirs.get("archives")
        if not archive_dir or not archive_dir.exists():
            return
        try:
            count = cleanup_temp_files(archive_dir, max_age_hours=1)
            if count > 0:
                logger.info("Stale archive temp files cleaned", extra={"count": count})
        except Exception as exc:
            result.warnings.append(f"Archive temp cleanup error: {exc}")

    def write_lock(self) -> None:
        """Write a lock file to indicate the application is running."""
        temp_dir = self.data_dirs.get("temp")
        if not temp_dir:
            return
        temp_dir.mkdir(parents=True, exist_ok=True)
        lock_path = temp_dir / "app.lock"
        lock_path.write_text(datetime.now().isoformat(), encoding="utf-8")

    def clear_lock(self) -> None:
        """Remove the lock file on clean shutdown."""
        lock_path = self.data_dirs.get("temp", Path()) / "app.lock"
        try:
            if lock_path.exists():
                lock_path.unlink()
        except OSError:
            pass
