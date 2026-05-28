from __future__ import annotations

import platform
import sys
from pathlib import Path


def resolve_project_root() -> Path:
    """Resolve the project root directory.

    In development: the git repository root.
    In production (PyInstaller): the directory containing the executable.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.resolve()
    return Path(__file__).resolve().parent.parent.parent


def resolve_data_directory(portable: bool = False) -> Path:
    """Resolve the user data directory.

    In portable mode, data sits next to the executable.
    In installed mode, uses the platform's standard app data directory.

    Args:
        portable: If True, use portable mode layout.

    Returns:
        Path to the user data directory.
    """
    if portable:
        base = resolve_project_root() / "data"
    else:
        system = platform.system()
        if system == "Windows":
            appdata = Path.home() / "AppData" / "Local"
            base = appdata / "oglg"
        elif system == "Linux":
            xdg = Path.home() / ".local" / "share"
            base = xdg / "oglg"
        else:
            base = Path.home() / ".oglg"
    return base


def ensure_data_directories(data_dir: Path) -> dict[str, Path]:
    """Create required runtime directory structure.

    Args:
        data_dir: Root data directory path.

    Returns:
        Dictionary of directory name to Path.
    """
    dirs = {
        "database": data_dir / "database",
        "archives": data_dir / "archives",
        "backups": data_dir / "backups",
        "generated_letters": data_dir / "generated_letters",
        "attachments": data_dir / "attachments",
        "logs": data_dir / "logs",
        "temp": data_dir / "temp",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def get_database_path(data_dir: Path) -> Path:
    """Get the SQLite database file path.

    Args:
        data_dir: Root data directory.

    Returns:
        Path to the SQLite database file.
    """
    return data_dir / "database" / "correspondence.db"


def get_config_path(data_dir: Path) -> Path:
    """Get the user configuration file path.

    Args:
        data_dir: Root data directory.

    Returns:
        Path to the user config JSON file.
    """
    return data_dir / "user_config.json"


def get_default_config_path() -> Path:
    """Get the bundled default configuration file path.

    Returns:
        Path to the defaults.json file.
    """
    return resolve_project_root() / "app" / "config" / "defaults.json"


def get_migrations_dir() -> Path:
    """Get the Alembic migrations directory path.

    Returns:
        Path to the migrations directory.
    """
    return resolve_project_root() / "app" / "database" / "migrations"


def get_log_dir(data_dir: Path) -> Path:
    """Get the log directory path.

    Args:
        data_dir: Root data directory.

    Returns:
        Path to the log directory.
    """
    return data_dir / "logs"


def is_portable_mode() -> bool:
    """Detect if running in portable mode.

    Returns True if a portable.txt marker file exists next to the executable,
    or if the --portable flag was passed (handled by CLI parsing).
    """
    marker = resolve_project_root() / "portable.txt"
    return marker.exists()
