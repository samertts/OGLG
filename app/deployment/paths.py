"""Deployment-aware path resolution for PyInstaller-packaged executables.

Handles three runtime modes:
  1. Development — runs from source tree
  2. Portable — executable with data/ alongside
  3. Installed — executable in Program Files, data in AppData
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

DeployMode = Literal["development", "portable", "installed"]


def get_deploy_mode() -> DeployMode:
    """Detect the current deployment mode at runtime.

    Returns:
        "development" when running from source,
        "portable" when a portable.txt marker exists,
        "installed" when running from a PyInstaller bundle without marker.
    """
    if not is_frozen():
        return "development"
    if _portable_marker_exists():
        return "portable"
    return "installed"


def get_runtime_dir() -> Path:
    """Get the directory containing the executable or script.

    In frozen mode: the directory containing the .exe.
    In development: the project root directory.
    """
    if is_frozen():
        return Path(sys.executable).parent.resolve()
    return Path(__file__).resolve().parent.parent.parent


def get_data_dir() -> Path:
    """Get the user data directory based on deployment mode.

    Portable mode: {runtime_dir}/data
    Installed mode (Windows): %LOCALAPPDATA%/oglg
    Installed mode (Linux): ~/.local/share/oglg
    Installed mode (macOS): ~/.oglg
    Development mode: {runtime_dir}/data
    """
    mode = get_deploy_mode()
    if mode == "portable":
        return get_runtime_dir() / "data"
    if mode == "development":
        return get_runtime_dir() / "data"
    return _get_platform_data_dir()


def resolve_bundled_path(relative: str) -> Path:
    """Resolve a path relative to the application bundle root.

    Works in both frozen and development modes.

    Args:
        relative: Relative path like "app/config/defaults.json"

    Returns:
        Absolute path within the application bundle.
    """
    return get_runtime_dir() / relative


def is_frozen() -> bool:
    """Check if running in a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def _portable_marker_exists() -> bool:
    marker = get_runtime_dir() / "portable.txt"
    return marker.exists()


def _get_platform_data_dir() -> Path:
    import platform as _platform

    system = _platform.system()
    if system == "Windows":
        appdata = Path.home() / "AppData" / "Local"
        return appdata / "oglg"
    if system == "Linux":
        xdg = Path.home() / ".local" / "share"
        return xdg / "oglg"
    return Path.home() / ".oglg"
