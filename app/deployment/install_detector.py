"""Installed mode detection and validation.

Detects if the application is running in installed mode and validates
the installation environment.
"""

from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("app.deployment.install_detector")


@dataclass
class InstallDetectionResult:
    """Result of installed mode detection and validation.

    Attributes:
        is_installed: Whether installed mode is detected.
        install_path: The detected installation directory.
        data_dir: The resolved application data directory.
        errors: Validation errors encountered.
        warnings: Non-fatal warnings about the installation.
    """

    is_installed: bool = False
    install_path: Path | None = None
    data_dir: Path | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class InstallDetector:
    """Detects and validates installed deployment mode.

    Installed mode is active when the application is running from a
    PyInstaller bundle without a portable marker (i.e. a proper system
    installation).
    """

    def __init__(self, runtime_dir: Path) -> None:
        """Initialize the detector with the runtime directory.

        Args:
            runtime_dir: The directory containing the application executable.
        """
        self.runtime_dir = runtime_dir.resolve()

    def detect(self) -> InstallDetectionResult:
        """Detect installed mode and validate the installation environment.

        Installed mode is assumed when the application is frozen
        (PyInstaller bundle) and no portable.txt marker exists.

        Returns:
            An InstallDetectionResult with detection and validation details.
        """
        result = InstallDetectionResult()

        if not self._is_frozen():
            return result

        portable_marker = self.runtime_dir / "portable.txt"
        if portable_marker.exists():
            return result

        result.is_installed = True
        result.install_path = self.runtime_dir
        result.data_dir = self._get_platform_data_dir()

        self._validate_install_environment(result)
        return result

    def _is_frozen(self) -> bool:
        """Check if running inside a PyInstaller bundle."""
        return getattr(sys, "frozen", False)

    def _validate_install_environment(self, result: InstallDetectionResult) -> None:
        """Check the installed environment for common issues.

        Validates that the data directory can be created and that
        the install path does not have permission problems.

        Args:
            result: The detection result to populate with issues.
        """
        if result.data_dir is None:
            return

        try:
            result.data_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            result.errors.append(f"Cannot create data directory: {exc}")

        if result.install_path and not os.access(str(result.install_path), os.R_OK):
            result.errors.append(f"Install path is not readable: {result.install_path}")

        if result.data_dir and result.data_dir.exists():
            if not os.access(str(result.data_dir), os.W_OK):
                result.errors.append(f"Data directory is not writable: {result.data_dir}")

    def get_install_path(self) -> Path | None:
        """Get the detected installation path.

        Returns:
            The runtime directory if frozen, None otherwise.
        """
        if self._is_frozen():
            return self.runtime_dir
        return None

    def get_program_data_dir(self) -> Path:
        """Get the system-wide program data directory for oglg.

        On Windows this is %PROGRAMDATA%/oglg.
        On Linux this is /etc/oglg.
        On macOS this is /Library/Application Support/oglg.

        Returns:
            Path to the program data directory.
        """
        system = platform.system()
        if system == "Windows":
            program_data = Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData"))
            return program_data / "oglg"
        if system == "Linux":
            return Path("/etc/oglg")
        return Path("/Library/Application Support/oglg")

    def get_local_app_data_dir(self) -> Path:
        """Get the per-user local application data directory for oglg.

        On Windows this is %LOCALAPPDATA%/oglg.
        On Linux this is ~/.local/share/oglg.
        On macOS this is ~/Library/Application Support/oglg.

        Returns:
            Path to the local application data directory.
        """
        system = platform.system()
        if system == "Windows":
            local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            return local / "oglg"
        if system == "Linux":
            xdg = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
            return xdg / "oglg"
        return Path.home() / "Library" / "Application Support" / "oglg"

    def is_admin_required(self) -> bool:
        """Determine whether administrator privileges are needed.

        Returns True if the install path is in a system-protected
        location such as Program Files.

        Returns:
            True if admin rights are required for the current install path.
        """
        if not self._is_frozen():
            return False
        system = platform.system()
        if system == "Windows":
            pf = Path(os.environ.get("ProgramFiles", "C:\\Program Files"))
            pfx86 = Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"))
            return str(self.runtime_dir).startswith(str(pf)) or str(self.runtime_dir).startswith(
                str(pfx86)
            )
        if system == "Linux":
            return str(self.runtime_dir).startswith("/usr/") or str(self.runtime_dir).startswith(
                "/opt/"
            )
        return str(self.runtime_dir).startswith("/Applications/")

    @staticmethod
    def _get_platform_data_dir() -> Path:
        """Get the platform-specific user data directory."""
        system = platform.system()
        if system == "Windows":
            local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            return local / "oglg"
        if system == "Linux":
            xdg = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
            return xdg / "oglg"
        return Path.home() / "Library" / "Application Support" / "oglg"
