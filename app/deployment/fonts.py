"""Arabic font management for deployment.

Handles registration and validation of bundled Arabic fonts
from the PyInstaller-packaged assets directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.deployment.paths import get_runtime_dir
from app.utils.logger import get_logger

logger = get_logger("app.deployment.fonts")


@dataclass(frozen=True)
class FontInfo:
    """Describes a bundled font file."""

    name: str
    filename: str
    path: Path
    style: str = "regular"


class FontManager:
    """Manages bundled font files and their registration."""

    REQUIRED_FONTS: list[dict[str, str]] = [
        {"name": "Amiri", "filename": "Amiri-Regular.ttf", "style": "regular"},
        {"name": "Amiri", "filename": "Amiri-Bold.ttf", "style": "bold"},
        {"name": "Amiri", "filename": "Amiri-Italic.ttf", "style": "italic"},
        {
            "name": "Noto Naskh Arabic",
            "filename": "NotoNaskhArabic-Regular.ttf",
            "style": "regular",
        },
        {"name": "Noto Naskh Arabic", "filename": "NotoNaskhArabic-Bold.ttf", "style": "bold"},
        {"name": "Traditional Arabic", "filename": "TraditionalArabic.ttf", "style": "regular"},
    ]

    def __init__(self, font_dir: Path | None = None) -> None:
        self.font_dir = font_dir or self._resolve_font_dir()

    def _resolve_font_dir(self) -> Path:
        return get_runtime_dir() / "assets" / "fonts"

    def get_available_fonts(self) -> list[FontInfo]:
        """List all bundled font files that exist on disk.

        Returns:
            List of FontInfo for found font files.
        """
        available: list[FontInfo] = []
        for spec in self.REQUIRED_FONTS:
            font_path = self.font_dir / spec["filename"]
            if font_path.exists():
                available.append(
                    FontInfo(
                        name=spec["name"],
                        filename=spec["filename"],
                        path=font_path,
                        style=spec["style"],
                    )
                )
        return available

    def get_missing_fonts(self) -> list[dict[str, str]]:
        """Identify required fonts that are not bundled.

        Returns:
            List of font specs missing from disk.
        """
        missing: list[dict[str, str]] = []
        for spec in self.REQUIRED_FONTS:
            font_path = self.font_dir / spec["filename"]
            if not font_path.exists():
                missing.append(spec)
        return missing

    def is_arabic_rendering_supported(self) -> bool:
        """Check if at least one Arabic font is available."""
        return any(
            font_path.exists()
            for spec in self.REQUIRED_FONTS
            if (font_path := self.font_dir / spec["filename"])
        )


def get_bundled_fonts() -> list[FontInfo]:
    """Convenience function to get all available bundled fonts."""
    return FontManager().get_available_fonts()


def register_application_fonts() -> bool:
    """Register bundled fonts with the OS font system.

    On Windows, uses AddFontResourceEx to load fonts privately
    without installing them system-wide.

    Returns:
        True if at least one font was registered successfully.
    """
    import platform as _platform

    if _platform.system() != "Windows":
        return True

    manager = FontManager()
    fonts = manager.get_available_fonts()
    if not fonts:
        logger.warning("No bundled fonts found to register")
        return False

    registered = 0
    for font in fonts:
        try:
            _register_font_win32(font.path)
            registered += 1
        except Exception as exc:
            logger.warning(
                "Font registration failed",
                extra={"font": font.filename, "error": str(exc)},
            )

    success = registered > 0
    logger.info(
        "Font registration complete",
        extra={"registered": registered, "total": len(fonts)},
    )
    return success


def _register_font_win32(font_path: Path) -> None:
    """Register a font file using the Windows AddFontResourceEx API.

    Uses FR_PRIVATE (0x10) flag so the font is available only to
    this process without system-wide installation.
    """
    import ctypes
    from ctypes import wintypes

    gdi32 = ctypes.windll.gdi32
    FR_PRIVATE = 0x10

    result = gdi32.AddFontResourceExW(
        wintypes.LPCWSTR(str(font_path)),
        wintypes.DWORD(FR_PRIVATE),
        None,
    )
    if result == 0:
        raise RuntimeError(f"AddFontResourceEx failed for {font_path}")
