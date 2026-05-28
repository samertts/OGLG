"""Archive directory initialization and validation.

Ensures archive directories exist with correct structure, validates
existing archive integrity, and provides archive metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("app.runtime.archive_initializer")


@dataclass
class ArchiveInitResult:
    """Result of an archive directory initialisation operation."""

    success: bool
    directories_created: list[str] = field(default_factory=list)
    existing_archives: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ArchiveInitializer:
    """Initialises and validates the archive directory structure.

    Creates required subdirectories, scans for existing archives,
    cleans up interrupted operations, and validates archive file
    integrity.
    """

    def __init__(
        self,
        archive_dir: Path,
        sub_dirs: list[str] | None = None,
    ) -> None:
        self._archive_dir = archive_dir
        self._sub_dirs = sub_dirs or ["letters", "attachments", "reports"]

    def initialize(self) -> ArchiveInitResult:
        """Create subdirectories and scan existing archives.

        Returns:
            ArchiveInitResult with creation and scanning details.
        """
        result = ArchiveInitResult(success=False)

        try:
            self.ensure_structure()
            result.existing_archives = self.scan_existing()
            interrupted = self.cleanup_interrupted()
            if interrupted > 0:
                result.warnings.append(f"Cleaned up {interrupted} interrupted archive files")
            warnings = self.validate_archive_integrity()
            result.warnings.extend(warnings)
            result.success = True
        except OSError as exc:
            result.errors.append(str(exc))
            logger.error("Archive initialization failed", extra={"error": str(exc)})

        logger.info(
            "Archive initialization completed",
            extra={
                "success": result.success,
                "directories_created": len(result.directories_created),
                "existing_archives": result.existing_archives,
                "errors": len(result.errors),
                "warnings": len(result.warnings),
            },
        )
        return result

    def ensure_structure(self) -> None:
        """Ensure all required subdirectories exist."""
        self._archive_dir.mkdir(parents=True, exist_ok=True)
        for sub in self._sub_dirs:
            path = self._archive_dir / sub
            path.mkdir(parents=True, exist_ok=True)
            logger.debug("Archive subdirectory ensured", extra={"path": str(path)})

    def scan_existing(self) -> int:
        """Count existing archive entries in the archive directory.

        Returns:
            Number of archive entries (files and subdirectories).
        """
        if not self._archive_dir.exists():
            return 0
        count = 0
        for sub in self._sub_dirs:
            path = self._archive_dir / sub
            if path.exists():
                count += sum(1 for _ in path.iterdir() if _.is_file())
        logger.debug("Existing archives scanned", extra={"count": count})
        return count

    def cleanup_interrupted(self) -> int:
        """Remove .tmp files left by interrupted archive operations.

        Returns:
            Number of temporary files removed.
        """
        removed = 0
        for sub in self._sub_dirs:
            path = self._archive_dir / sub
            if not path.exists():
                continue
            for tmp_file in path.glob("*.tmp"):
                try:
                    tmp_file.unlink()
                    removed += 1
                except OSError as exc:
                    logger.warning(
                        "Failed to remove temp file",
                        extra={"path": str(tmp_file), "error": str(exc)},
                    )
        if removed > 0:
            logger.info("Interrupted archive temps removed", extra={"count": removed})
        return removed

    def validate_archive_integrity(self) -> list[str]:
        """Check for corrupted archive files in the archive directory.

        A file is considered potentially corrupted if it has zero
        bytes or an unrecognised extension.

        Returns:
            List of warning messages for suspected corrupted files.
        """
        warnings: list[str] = []
        known_extensions = {".pdf", ".txt", ".docx", ".json", ".xml", ".zip", ".jpg", ".png"}
        for sub in self._sub_dirs:
            path = self._archive_dir / sub
            if not path.exists():
                continue
            for entry in path.iterdir():
                if not entry.is_file():
                    continue
                if entry.stat().st_size == 0:
                    warnings.append(f"Empty file: {entry}")
                    continue
                if entry.suffix.lower() not in known_extensions and entry.suffix != "":
                    warnings.append(f"Unknown extension: {entry}")
        return warnings
