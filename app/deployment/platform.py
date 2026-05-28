"""Platform detection and Windows version compatibility.

Supports Windows 7 through Windows 11 detection and capability checks.
"""

from __future__ import annotations

import platform as _platform
import sys
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PlatformInfo:
    """Detected platform information."""

    system: str
    release: str
    version: str
    machine: str
    is_frozen: bool
    python_version: str
    is_admin: bool = False

    @property
    def is_windows(self) -> bool:
        return self.system == "Windows"

    @property
    def is_linux(self) -> bool:
        return self.system == "Linux"

    @property
    def windows_major(self) -> int:
        if not self.is_windows:
            return 0
        parts = self.version.split(".")
        return int(parts[0]) if parts else 0

    @property
    def windows_minor(self) -> int:
        if not self.is_windows:
            return 0
        parts = self.version.split(".")
        return int(parts[1]) if len(parts) > 1 else 0

    @property
    def windows_build(self) -> int:
        if not self.is_windows:
            return 0
        parts = self.version.split(".")
        return int(parts[2]) if len(parts) > 2 else 0

    @property
    def display_name(self) -> str:
        if not self.is_windows:
            return f"{self.system} {self.release}"
        major = self.windows_major
        build = self.windows_build
        if major == 10 and build >= 22000:
            return "Windows 11"
        if major == 10:
            return "Windows 10"
        if major == 6 and self.windows_minor == 1:
            return "Windows 7"
        if major == 6 and self.windows_minor == 2:
            return "Windows 8"
        if major == 6 and self.windows_minor == 3:
            return "Windows 8.1"
        return f"Windows {major}.{self.windows_minor}"


def detect_platform() -> PlatformInfo:
    """Detect the current runtime platform.

    Returns:
        PlatformInfo with full system details.
    """
    return PlatformInfo(
        system=_platform.system(),
        release=_platform.release(),
        version=_platform.version(),
        machine=_platform.machine(),
        is_frozen=getattr(sys, "frozen", False),
        python_version=sys.version,
        is_admin=_check_admin(),
    )


def is_windows_7_compatible(info: PlatformInfo | None = None) -> bool:
    """Check if running on Windows 7 or later."""
    if info is None:
        info = detect_platform()
    if not info.is_windows:
        return False
    return (info.windows_major == 6 and info.windows_minor >= 1) or info.windows_major >= 10


def is_windows_8_compatible(info: PlatformInfo | None = None) -> bool:
    """Check if running on Windows 8 or later."""
    if info is None:
        info = detect_platform()
    if not info.is_windows:
        return False
    return (info.windows_major == 6 and info.windows_minor >= 2) or info.windows_major >= 10


def is_windows_10_compatible(info: PlatformInfo | None = None) -> bool:
    """Check if running on Windows 10 or later."""
    if info is None:
        info = detect_platform()
    if not info.is_windows:
        return False
    return info.windows_major >= 10


def is_windows_11_compatible(info: PlatformInfo | None = None) -> bool:
    """Check if running on Windows 11 or later."""
    if info is None:
        info = detect_platform()
    if not info.is_windows:
        return False
    return info.windows_major >= 10 and info.windows_build >= 22000


def _check_admin() -> bool:
    """Check if the process is running with administrator privileges.

    Works on both Windows and POSIX systems.
    """
    try:
        import os as _os
        if _platform.system() == "Windows":
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        return _os.geteuid() == 0
    except Exception:
        return False
