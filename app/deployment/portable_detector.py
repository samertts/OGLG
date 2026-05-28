"""Portable mode detection and validation.

Detects if the application is running in portable mode and validates
that the portable environment is correctly set up.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("app.deployment.portable_detector")

_PORTABLE_MARKER = "portable.txt"
_PORTABLE_MARKER_CONTENT = "portable"
_MIN_DISK_SPACE_MB = 50


@dataclass
class PortableDetectionResult:
    """Result of portable mode detection and validation.

    Attributes:
        is_portable: Whether portable mode is active.
        marker_path: Path to the portable marker file, if found.
        data_dir: Resolved data directory path, if determined.
        errors: Validation errors encountered.
        warnings: Non-fatal warnings about the environment.
    """

    is_portable: bool = False
    marker_path: Path | None = None
    data_dir: Path | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class PortableDetector:
    """Detects and validates portable deployment mode.

    Portable mode is indicated by the presence of a portable.txt marker
    file in the runtime directory or one of its parent directories.
    """

    def __init__(self, runtime_dir: Path) -> None:
        """Initialize the detector with the runtime directory.

        Args:
            runtime_dir: The directory containing the application executable.
        """
        self.runtime_dir = runtime_dir.resolve()

    def detect(self) -> PortableDetectionResult:
        """Detect portable mode and validate the environment.

        Returns:
            A PortableDetectionResult with detection and validation details.
        """
        result = PortableDetectionResult()
        marker = self._find_marker()
        if marker is None:
            return result

        result.is_portable = True
        result.marker_path = marker
        result.data_dir = marker.parent / "data"

        if not self._check_portable_marker_content(marker):
            result.errors.append(f"Marker file has invalid content: {marker}")

        self._validate_portable_environment(result)
        return result

    def _find_marker(self) -> Path | None:
        """Search for portable.txt in the runtime directory and its parents.

        Returns:
            Path to the marker file, or None if not found.
        """
        candidate = self.runtime_dir / _PORTABLE_MARKER
        if candidate.is_file():
            return candidate

        for parent in self.runtime_dir.parents:
            candidate = parent / _PORTABLE_MARKER
            if candidate.is_file():
                return candidate

        return None

    def _validate_portable_environment(self, result: PortableDetectionResult) -> None:
        """Check that the portable data directory is valid.

        Verifies the data directory is writable and has sufficient
        free disk space.

        Args:
            result: The detection result to populate with issues.
        """
        if result.data_dir is None:
            return

        if result.data_dir.exists() and not os.access(str(result.data_dir), os.W_OK):
            result.errors.append(f"Data directory is not writable: {result.data_dir}")

        try:
            result.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            result.errors.append(f"Cannot create data directory: {exc}")
            return

        try:
            stat = os.statvfs(str(result.data_dir))
            free_mb = (stat.f_bavail * stat.f_frsize) // (1024 * 1024)
            if free_mb < _MIN_DISK_SPACE_MB:
                result.warnings.append(
                    f"Low disk space: {free_mb} MB free, "
                    f"minimum {_MIN_DISK_SPACE_MB} MB recommended"
                )
        except OSError:
            result.warnings.append("Could not check disk space")

    def _check_portable_marker_content(self, marker_path: Path) -> bool:
        """Validate the content of the portable marker file.

        The marker file should contain exactly the text "portable".

        Args:
            marker_path: Path to the marker file.

        Returns:
            True if content is valid, False otherwise.
        """
        try:
            content = marker_path.read_text(encoding="utf-8").strip()
            return content == _PORTABLE_MARKER_CONTENT
        except OSError:
            return False

    def create_marker(self) -> Path:
        """Create the portable.txt marker file.

        Returns:
            Path to the newly created marker file.

        Raises:
            OSError: If the marker file cannot be created.
        """
        marker_path = self.runtime_dir / _PORTABLE_MARKER
        marker_path.write_text(_PORTABLE_MARKER_CONTENT + "\n", encoding="utf-8")
        logger.info("Portable marker created", extra={"path": str(marker_path)})
        return marker_path

    def remove_marker(self) -> None:
        """Remove the portable.txt marker file if it exists."""
        marker_path = self.runtime_dir / _PORTABLE_MARKER
        if marker_path.exists():
            marker_path.unlink()
            logger.info("Portable marker removed", extra={"path": str(marker_path)})

    def is_valid_portable_root(self, path: Path) -> bool:
        """Check whether a given directory is a valid portable root.

        A valid portable root must contain the portable.txt marker
        and a data subdirectory.

        Args:
            path: The candidate directory.

        Returns:
            True if the path is a valid portable root.
        """
        resolved = path.resolve()
        marker = resolved / _PORTABLE_MARKER
        data = resolved / "data"
        return marker.is_file() and data.is_dir()
