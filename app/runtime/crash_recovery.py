"""Enhanced crash recovery and integrity validation.

Detects unclean shutdowns, validates database integrity, cleans up
stale artifacts, and restores safe state before normal startup.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from pathlib import Path

from app.runtime.recovery import CrashRecoveryBootstrap
from app.utils.file_utils import cleanup_temp_files
from app.utils.logger import get_logger

logger = get_logger("app.runtime.crash_recovery")


class RecoveryAction(enum.Enum):
    """Actions that may be taken during a recovery sequence."""

    NONE = "none"
    LOCK_CLEARED = "lock_cleared"
    TEMP_CLEANED = "temp_cleaned"
    DB_REPAIRED = "db_repaired"
    ARCHIVE_CLEANED = "archive_cleaned"
    PARTIAL_WRITE_ROLLBACK = "partial_write_rollback"


@dataclass
class RecoveryResult:
    """Result of a crash recovery execution."""

    recovered: bool
    actions: list[RecoveryAction] = field(default_factory=list)
    integrity_ok: bool = False
    temp_files_cleaned: int = 0
    stale_lock_cleared: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class CrashRecoveryManager:
    """High-level crash recovery orchestrator.

    Detects unclean shutdowns, delegates low-level lock and database
    operations to CrashRecoveryBootstrap, and provides startup/cleanup
    marker management for crash detection.
    """

    def __init__(
        self,
        data_dirs: dict[str, Path],
        db_path: Path | None = None,
    ) -> None:
        self._data_dirs = data_dirs
        self._db_path = db_path
        self._bootstrap = CrashRecoveryBootstrap(
            data_dirs=data_dirs,
            db_path=db_path,
        )

    def execute(self) -> RecoveryResult:
        """Execute the full crash recovery sequence.

        Returns:
            RecoveryResult with all actions taken and integrity status.
        """
        result = RecoveryResult(recovered=False, integrity_ok=False)
        crashed = self._detect_crash()

        if not crashed:
            logger.info("No crash detected")
            result.integrity_ok = True
            return result

        logger.info("Crash detected, starting recovery")

        self._clear_stale_locks(result)
        self._validate_db_integrity(result)
        self._cleanup_orphan_temp(result)
        self._recover_interrupted_archives(result)
        self._rollback_partial_writes(result)

        result.recovered = (
            result.integrity_ok
            or result.temp_files_cleaned > 0
            or result.stale_lock_cleared
            or len(result.actions) > 0
        )

        logger.info(
            "Crash recovery completed",
            extra={
                "recovered": result.recovered,
                "actions": [a.value for a in result.actions],
                "integrity_ok": result.integrity_ok,
                "temp_cleaned": result.temp_files_cleaned,
                "lock_cleared": result.stale_lock_cleared,
            },
        )
        return result

    def _detect_crash(self) -> bool:
        """Check for crash markers indicating an unclean shutdown.

        Returns:
            True if a crash marker is present.
        """
        temp_dir = self._data_dirs.get("temp")
        if not temp_dir:
            return False
        lock_path = temp_dir / "app.lock"
        marker_path = temp_dir / ".startup_marker"
        if lock_path.exists():
            return True
        if marker_path.exists():
            return True
        logger.debug("No crash markers found")
        return False

    def _clear_stale_locks(self, result: RecoveryResult) -> None:
        lock_path = self._data_dirs.get("temp", Path()) / "app.lock"
        if not lock_path.exists():
            return
        try:
            lock_path.unlink()
            result.stale_lock_cleared = True
            result.actions.append(RecoveryAction.LOCK_CLEARED)
            result.warnings.append("Stale lock file cleared")
            logger.info("Stale lock file cleared")
        except OSError as exc:
            result.errors.append(f"Failed to clear lock: {exc}")

    def _validate_db_integrity(self, result: RecoveryResult) -> None:
        if not self._db_path or not self._db_path.exists():
            result.integrity_ok = True
            return
        try:
            bootstrap_result = self._bootstrap.run_recovery()
            result.integrity_ok = bootstrap_result.integrity_ok
            if not result.integrity_ok:
                result.errors.extend(bootstrap_result.errors)
            if bootstrap_result.stale_lock_cleared:
                result.stale_lock_cleared = True
                if RecoveryAction.LOCK_CLEARED not in result.actions:
                    result.actions.append(RecoveryAction.LOCK_CLEARED)
        except Exception as exc:
            result.errors.append(f"DB integrity check failed: {exc}")
            result.integrity_ok = False

    def _cleanup_orphan_temp(self, result: RecoveryResult) -> None:
        temp_dir = self._data_dirs.get("temp")
        if not temp_dir or not temp_dir.exists():
            return
        try:
            count = cleanup_temp_files(temp_dir, max_age_hours=0)
            result.temp_files_cleaned = count
            if count > 0:
                result.actions.append(RecoveryAction.TEMP_CLEANED)
                logger.info("Orphaned temp files cleaned", extra={"count": count})
        except Exception as exc:
            result.warnings.append(f"Orphan temp cleanup error: {exc}")

    def _recover_interrupted_archives(self, result: RecoveryResult) -> None:
        archive_dir = self._data_dirs.get("archives")
        if not archive_dir or not archive_dir.exists():
            return
        try:
            count = cleanup_temp_files(archive_dir, max_age_hours=1)
            if count > 0:
                result.actions.append(RecoveryAction.ARCHIVE_CLEANED)
                logger.info("Interrupted archive temps cleaned", extra={"count": count})
        except Exception as exc:
            result.warnings.append(f"Archive recovery error: {exc}")

    def _rollback_partial_writes(self, result: RecoveryResult) -> None:
        for dir_name, directory in self._data_dirs.items():
            if not directory.exists():
                continue
            try:
                count = 0
                for tmp_file in directory.glob("*.tmp"):
                    tmp_file.unlink()
                    count += 1
                if count > 0:
                    result.actions.append(RecoveryAction.PARTIAL_WRITE_ROLLBACK)
                    logger.info(
                        "Partial writes rolled back",
                        extra={"directory": dir_name, "count": count},
                    )
            except OSError as exc:
                result.warnings.append(f"Rollback error in {dir_name}: {exc}")

    def write_startup_marker(self) -> None:
        """Write a startup marker file to enable crash detection."""
        temp_dir = self._data_dirs.get("temp")
        if not temp_dir:
            return
        temp_dir.mkdir(parents=True, exist_ok=True)
        marker = temp_dir / ".startup_marker"
        try:
            marker.write_text("running", encoding="utf-8")
            logger.debug("Startup marker written")
        except OSError as exc:
            logger.warning("Failed to write startup marker", extra={"error": str(exc)})

    def clear_startup_marker(self) -> None:
        """Remove the startup marker on clean shutdown."""
        temp_dir = self._data_dirs.get("temp")
        if not temp_dir:
            return
        marker = temp_dir / ".startup_marker"
        try:
            if marker.exists():
                marker.unlink()
                logger.debug("Startup marker cleared")
        except OSError:
            pass
