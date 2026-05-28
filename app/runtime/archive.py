"""Archive directory initialization and validation.

Ensures the archive directory structure is correctly initialized
at startup and validates archive integrity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.utils.file_utils import ensure_directory
from app.utils.logger import get_logger

logger = get_logger("app.runtime.archive")


@dataclass
class ArchiveInitResult:
    """Result of archive directory initialization."""

    created: list[str] = field(default_factory=list)
    existing: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class ArchiveDirectoryInitializer:
    """Initializes and validates the archive directory structure.

    Creates the required subdirectory hierarchy for archived letters
    and verifies write permissions.
    """

    SUBDIRECTORIES = [
        "yearly",
        "monthly",
        "corrupted",
        "pending",
    ]

    def __init__(self, archive_dir: Path) -> None:
        self.archive_dir = archive_dir

    def initialize(self) -> ArchiveInitResult:
        """Create the full archive directory hierarchy.

        Returns:
            ArchiveInitResult with lists of created and existing paths.
        """
        result = ArchiveInitResult()

        try:
            if ensure_directory(self.archive_dir):
                result.created.append(str(self.archive_dir))
            else:
                result.existing.append(str(self.archive_dir))
        except OSError as exc:
            result.errors.append(f"Failed to create archive root: {exc}")
            return result

        for subdir in self.SUBDIRECTORIES:
            path = self.archive_dir / subdir
            try:
                if ensure_directory(path):
                    result.created.append(str(path))
                else:
                    result.existing.append(str(path))
            except OSError as exc:
                result.errors.append(f"Failed to create {subdir}: {exc}")

        if result.errors:
            logger.error("Archive init had errors", extra={"errors": result.errors})
        else:
            logger.info(
                "Archive directory initialized",
                extra={"created": len(result.created), "existing": len(result.existing)},
            )

        return result

    def validate_writable(self) -> bool:
        """Verify the archive directory is writable.

        Attempts to create and remove a test file.

        Returns:
            True if writable, False otherwise.
        """
        try:
            test_file = self.archive_dir / ".write_test"
            test_file.write_bytes(b"test")
            test_file.unlink()
            return True
        except OSError:
            return False

    def get_subdirectory(self, name: str) -> Path:
        """Get a named subdirectory, creating it if needed.

        Args:
            name: Subdirectory name (one of SUBDIRECTORIES).

        Returns:
            Path to the subdirectory.
        """
        path = self.archive_dir / name
        ensure_directory(path)
        return path

    def get_yearly_dir(self, year: int) -> Path:
        """Get or create a year-based archive subdirectory.

        Args:
            year: Four-digit year.

        Returns:
            Path to the year subdirectory.
        """
        path = self.archive_dir / "yearly" / str(year)
        ensure_directory(path)
        return path

    def get_monthly_dir(self, year: int, month: int) -> Path:
        """Get or create a month-based archive subdirectory.

        Args:
            year: Four-digit year.
            month: Month number (1-12).

        Returns:
            Path to the month subdirectory.
        """
        path = self.archive_dir / "monthly" / f"{year}-{month:02d}"
        ensure_directory(path)
        return path
