"""Centralized path resolution for all runtime scenarios.

Provides a single source of truth for resolving application paths
across development, portable, and installed deployment modes.
"""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path

from app.runtime.runtime_mode import RuntimeMode
from app.utils.logger import get_logger

logger = get_logger("app.runtime.path_resolver")


@dataclass
class PathResolver:
    """Resolves application paths based on runtime mode.

    Attributes:
        mode: The current RuntimeMode (Development, Portable, Installed).
        app_root: The resolved application root directory.
    """

    mode: RuntimeMode
    app_root: Path
    _data_dir_override: Path | None = field(default=None, repr=False)

    # ---- Directory resolvers -------------------------------------------------

    def resolve_data_dir(self) -> Path:
        """Resolve the root data directory.

        Portable:  ``{app_root}/data``
        Installed: platform-specific app data dir (``~/.local/share/oglg``
                   on Linux, ``%LOCALAPPDATA%/oglg`` on Windows,
                   ``~/.oglg`` on macOS / other).
        Dev:       ``{app_root}/data``
        """
        if self._data_dir_override is not None:
            return self._data_dir_override
        if self.mode == RuntimeMode.PORTABLE:
            return self.app_root / "data"
        if self.mode == RuntimeMode.INSTALLED:
            return self.get_platform_data_dir()
        return self.app_root / "data"

    def resolve_config_dir(self) -> Path:
        """Resolve the configuration directory (``{data_dir}/config``)."""
        return self.resolve_data_dir() / "config"

    def resolve_database_dir(self) -> Path:
        """Resolve the database directory (``{data_dir}/database``)."""
        return self.resolve_data_dir() / "database"

    def resolve_logs_dir(self) -> Path:
        """Resolve the log directory (``{data_dir}/logs``)."""
        return self.resolve_data_dir() / "logs"

    def resolve_temp_dir(self) -> Path:
        """Resolve the temporary files directory (``{data_dir}/temp``)."""
        return self.resolve_data_dir() / "temp"

    def resolve_backups_dir(self) -> Path:
        """Resolve the backups directory (``{data_dir}/backups``)."""
        return self.resolve_data_dir() / "backups"

    def resolve_archives_dir(self) -> Path:
        """Resolve the archives directory (``{data_dir}/archives``)."""
        return self.resolve_data_dir() / "archives"

    def resolve_assets_dir(self) -> Path:
        """Resolve the bundled assets directory (``{app_root}/app/assets``)."""
        return self.app_root / "app" / "assets"

    def resolve_fonts_dir(self) -> Path:
        """Resolve the bundled fonts directory (``{assets_dir}/fonts``)."""
        return self.resolve_assets_dir() / "fonts"

    def resolve_templates_dir(self) -> Path:
        """Resolve the bundled templates directory (``{app_root}/app/templates``)."""
        return self.app_root / "app" / "templates"

    # ---- File resolvers ------------------------------------------------------

    def resolve_default_config_path(self) -> Path:
        """Resolve the bundled default configuration file."""
        return self.app_root / "app" / "config" / "defaults.json"

    def resolve_user_config_path(self) -> Path:
        """Resolve the user configuration file path."""
        return self.resolve_config_dir() / "user_config.json"

    def resolve_database_path(self) -> Path:
        """Resolve the SQLite database file path."""
        return self.resolve_database_dir() / "correspondence.db"

    def resolve_bundled_path(self, relative: str) -> Path:
        """Resolve a path relative to the application root.

        Args:
            relative: Relative path (e.g. ``"app/config/defaults.json"``).

        Returns:
            Absolute ``Path`` under ``app_root``.
        """
        return (self.app_root / relative).resolve()

    # ---- Aggregate -----------------------------------------------------------

    def get_all_directories(self) -> dict[str, Path]:
        """Return a dictionary of all resolved directories.

        Returns:
            Mapping of directory name (e.g. ``"data"``, ``"logs"``) to Path.
        """
        return {
            "data": self.resolve_data_dir(),
            "config": self.resolve_config_dir(),
            "database": self.resolve_database_dir(),
            "logs": self.resolve_logs_dir(),
            "temp": self.resolve_temp_dir(),
            "backups": self.resolve_backups_dir(),
            "archives": self.resolve_archives_dir(),
            "assets": self.resolve_assets_dir(),
            "fonts": self.resolve_fonts_dir(),
            "templates": self.resolve_templates_dir(),
        }

    # ---- Static helpers ------------------------------------------------------

    @staticmethod
    def get_platform_data_dir() -> Path:
        """Return the platform-specific application data directory.

        Returns:
            ``~/.local/share/oglg`` on Linux,
            ``%LOCALAPPDATA%/oglg`` on Windows,
            ``~/.oglg`` on macOS / other systems.
        """
        system = platform.system()
        if system == "Windows":
            return Path.home() / "AppData" / "Local" / "oglg"
        if system == "Linux":
            return Path.home() / ".local" / "share" / "oglg"
        return Path.home() / ".oglg"

    @staticmethod
    def resolve_project_root() -> Path:
        """Resolve the project root directory.

        In development (not frozen): the repository root (parent of
        ``app/runtime/path_resolver.py``).

        In production (frozen / PyInstaller): the directory containing
        the executable.

        Returns:
            Absolute path to the project root.
        """
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent.resolve()
        return Path(__file__).resolve().parent.parent.parent


# ---- Factory -----------------------------------------------------------------


def create_path_resolver(
    mode: RuntimeMode,
    app_root_override: Path | None = None,
    data_dir_override: Path | None = None,
) -> PathResolver:
    """Create a fully initialised PathResolver.

    Args:
        mode: The RuntimeMode to use for resolution.
        app_root_override: Explicit application root (auto-detected if ``None``).
        data_dir_override: Explicit data directory (auto-resolved if ``None``).

    Returns:
        A configured PathResolver instance.
    """
    if app_root_override is not None:
        app_root = app_root_override
    elif getattr(sys, "frozen", False):
        app_root = Path(sys.executable).parent.resolve()
    else:
        app_root = PathResolver.resolve_project_root()

    resolver = PathResolver(mode=mode, app_root=app_root, _data_dir_override=data_dir_override)

    logger.debug(
        "PathResolver created",
        extra={
            "mode": mode.value,
            "app_root": str(app_root),
            "data_dir": str(resolver.resolve_data_dir()),
        },
    )

    return resolver
