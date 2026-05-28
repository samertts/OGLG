"""Runtime mode detection for the Correspondence System.

Defines the three runtime modes (Development, Portable, Installed)
and provides detection logic for each.
"""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("app.runtime.runtime_mode")


class RuntimeMode(Enum):
    """Runtime deployment modes for the Correspondence System.

    Attributes:
        DEVELOPMENT: Running from source (not frozen).
        PORTABLE: Running from a frozen executable with portable.txt marker.
        INSTALLED: Running from a frozen executable without portable marker.
    """

    DEVELOPMENT = "DEVELOPMENT"
    PORTABLE = "PORTABLE"
    INSTALLED = "INSTALLED"


def is_frozen() -> bool:
    """Check if the application is bundled with PyInstaller or similar.

    Returns:
        True if running from a frozen (bundled) executable.
    """
    return getattr(sys, "frozen", False)


def detect_runtime_mode() -> RuntimeMode:
    """Detect the current runtime mode based on the execution environment.

    Detection priority:
        1. If not frozen (``sys.frozen`` is False / absent) → DEVELOPMENT.
        2. If ``portable.txt`` marker exists next to the executable → PORTABLE.
        3. Otherwise → INSTALLED.

    Returns:
        The detected RuntimeMode.
    """
    if not is_frozen():
        logger.debug("Runtime mode detected as DEVELOPMENT (not frozen)")
        return RuntimeMode.DEVELOPMENT

    exe_dir = Path(sys.executable).parent.resolve()
    portable_marker = exe_dir / "portable.txt"
    if portable_marker.exists():
        logger.debug("Runtime mode detected as PORTABLE (marker found)")
        return RuntimeMode.PORTABLE

    logger.debug("Runtime mode detected as INSTALLED (frozen, no portable marker)")
    return RuntimeMode.INSTALLED
