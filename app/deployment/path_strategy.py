"""Path selection strategy for deployment modes.

Selects appropriate path resolution strategy based on the detected
deployment mode (development, portable, or installed).
"""

from __future__ import annotations

import os
import platform
from abc import ABC, abstractmethod
from pathlib import Path

from app.runtime.runtime_mode import RuntimeMode
from app.utils.logger import get_logger

logger = get_logger("app.deployment.path_strategy")


class PathStrategy(ABC):
    """Abstract base for deployment-mode-specific path resolution."""

    @abstractmethod
    def resolve_data_dir(self) -> Path:
        """Resolve the root data directory for this deployment mode."""

    @abstractmethod
    def resolve_config_dir(self) -> Path:
        """Resolve the configuration directory."""

    @abstractmethod
    def resolve_logs_dir(self) -> Path:
        """Resolve the logs directory."""

    @abstractmethod
    def resolve_temp_dir(self) -> Path:
        """Resolve the temporary files directory."""

    @abstractmethod
    def resolve_database_dir(self) -> Path:
        """Resolve the database directory."""

    @abstractmethod
    def resolve_backups_dir(self) -> Path:
        """Resolve the backups directory."""

    @abstractmethod
    def resolve_archives_dir(self) -> Path:
        """Resolve the archives directory."""


class DevelopmentPathStrategy(PathStrategy):
    """Path strategy for development mode.

    Uses ``data/`` relative to the project root.
    """

    def __init__(self, runtime_dir: Path) -> None:
        """Initialize with the project runtime directory.

        Args:
            runtime_dir: The project root directory.
        """
        self.runtime_dir = runtime_dir

    def resolve_data_dir(self) -> Path:
        return self.runtime_dir / "data"

    def resolve_config_dir(self) -> Path:
        return self.runtime_dir / "data" / "config"

    def resolve_logs_dir(self) -> Path:
        return self.runtime_dir / "data" / "logs"

    def resolve_temp_dir(self) -> Path:
        return self.runtime_dir / "data" / "temp"

    def resolve_database_dir(self) -> Path:
        return self.runtime_dir / "data" / "database"

    def resolve_backups_dir(self) -> Path:
        return self.runtime_dir / "data" / "backups"

    def resolve_archives_dir(self) -> Path:
        return self.runtime_dir / "data" / "archives"


class PortablePathStrategy(PathStrategy):
    """Path strategy for portable mode.

    Uses ``data/`` alongside the executable.
    """

    def __init__(self, runtime_dir: Path) -> None:
        """Initialize with the portable runtime directory.

        Args:
            runtime_dir: The directory containing the portable executable.
        """
        self.runtime_dir = runtime_dir

    def resolve_data_dir(self) -> Path:
        return self.runtime_dir / "data"

    def resolve_config_dir(self) -> Path:
        return self.runtime_dir / "data" / "config"

    def resolve_logs_dir(self) -> Path:
        return self.runtime_dir / "data" / "logs"

    def resolve_temp_dir(self) -> Path:
        return self.runtime_dir / "data" / "temp"

    def resolve_database_dir(self) -> Path:
        return self.runtime_dir / "data" / "database"

    def resolve_backups_dir(self) -> Path:
        return self.runtime_dir / "data" / "backups"

    def resolve_archives_dir(self) -> Path:
        return self.runtime_dir / "data" / "archives"


class InstalledPathStrategy(PathStrategy):
    """Path strategy for installed (system-wide) mode.

    Uses platform-standard application data directories.
    """

    def __init__(self, runtime_dir: Path) -> None:
        """Initialize with the installation runtime directory.

        Args:
            runtime_dir: The directory where the application is installed.
        """
        self.runtime_dir = runtime_dir

    def resolve_data_dir(self) -> Path:
        return self._get_platform_data_dir()

    def resolve_config_dir(self) -> Path:
        return self._get_platform_config_dir()

    def resolve_logs_dir(self) -> Path:
        return self._get_platform_data_dir() / "logs"

    def resolve_temp_dir(self) -> Path:
        return self._get_platform_data_dir() / "temp"

    def resolve_database_dir(self) -> Path:
        return self._get_platform_data_dir() / "database"

    def resolve_backups_dir(self) -> Path:
        return self._get_platform_data_dir() / "backups"

    def resolve_archives_dir(self) -> Path:
        return self._get_platform_data_dir() / "archives"

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

    @staticmethod
    def _get_platform_config_dir() -> Path:
        """Get the platform-specific config directory."""
        system = platform.system()
        if system == "Windows":
            appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
            return appdata / "oglg" / "config"
        if system == "Linux":
            xdg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
            return xdg / "oglg"
        return Path.home() / "Library" / "Preferences" / "oglg"


def get_path_strategy(mode: RuntimeMode, runtime_dir: Path) -> PathStrategy:
    """Factory function: return the appropriate PathStrategy for the given mode.

    Args:
        mode: The active RuntimeMode.
        runtime_dir: The runtime base directory.

    Returns:
        A PathStrategy implementation matching the deployment mode.
    """
    strategy_map: dict[RuntimeMode, type[PathStrategy]] = {
        RuntimeMode.DEVELOPMENT: DevelopmentPathStrategy,
        RuntimeMode.PORTABLE: PortablePathStrategy,
        RuntimeMode.INSTALLED: InstalledPathStrategy,
    }
    strategy_cls = strategy_map[mode]
    logger.debug(
        "Path strategy selected",
        extra={"mode": mode.value, "strategy": strategy_cls.__name__},
    )
    return strategy_cls(runtime_dir)
