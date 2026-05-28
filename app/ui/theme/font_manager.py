from __future__ import annotations

import itertools
from pathlib import Path

from loguru import logger

from app.ui.theme.typography import TypeScale

try:
    from PySide6.QtGui import QFont, QFontDatabase
except ImportError:
    QFont = None
    QFontDatabase = None


class FontManager:
    _instance: FontManager | None = None

    def __init__(self) -> None:
        self._arabic_fonts_loaded = False
        self._fonts: dict[str, QFont] = {}

    @classmethod
    def get_instance(cls) -> FontManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_arabic_fonts(self, font_dir: Path | None = None) -> bool:
        if self._arabic_fonts_loaded:
            return True
        if QFontDatabase is None:
            return False
        db = QFontDatabase()
        loaded = 0
        if font_dir and font_dir.is_dir():
            for f in itertools.chain(
                font_dir.glob("*.ttf"),
                font_dir.glob("*.otf"),
                font_dir.glob("*.TTF"),
                font_dir.glob("*.OTF"),
            ):
                fid = db.addApplicationFont(str(f))
                if fid >= 0:
                    loaded += 1
        self._arabic_fonts_loaded = True
        logger.debug("Arabic fonts loaded", extra={"count": loaded})
        return loaded > 0

    def get_font(
        self,
        type_scale: TypeScale,
        size_key: str = "body_medium",
        is_arabic: bool = False,
        bold: bool = False,
    ) -> QFont:
        cache_key = f"{size_key}_{is_arabic}_{bold}"
        if cache_key in self._fonts:
            return self._fonts[cache_key]
        family = type_scale.font_family_arabic if is_arabic else type_scale.font_family
        size = getattr(type_scale, f"{size_key}_size", 14)
        weight_str = getattr(type_scale, f"{size_key}_weight", "400")
        weight = self._parse_weight(weight_str)
        if bold:
            weight = QFont.Bold
        font = QFont(family, size, weight)
        self._fonts[cache_key] = font
        return font

    def get_mono_font(self, type_scale: TypeScale, is_arabic: bool = False) -> QFont:
        family = type_scale.font_family_arabic_mono if is_arabic else type_scale.font_family_mono
        return QFont(family, type_scale.code_size, QFont.Normal)

    def get_arabic_adjusted_scale(self, type_scale: TypeScale) -> TypeScale:
        adjustments = TypeScale.ARABIC_ADJUSTMENTS
        adjusted = {}
        for k, v in type_scale.__dict__.items():
            if k in adjustments:
                adjusted[k] = v + adjustments[k]
            else:
                adjusted[k] = v
        return TypeScale(**adjusted)

    @staticmethod
    def _parse_weight(weight_str: str) -> int:
        mapping = {
            "100": QFont.Thin if QFont else 0,
            "200": QFont.ExtraLight if QFont else 0,
            "300": QFont.Light if QFont else 0,
            "400": QFont.Normal if QFont else 0,
            "500": QFont.Medium if QFont else 0,
            "600": QFont.DemiBold if QFont else 0,
            "700": QFont.Bold if QFont else 0,
            "800": QFont.ExtraBold if QFont else 0,
            "900": QFont.Black if QFont else 0,
        }
        return mapping.get(weight_str, QFont.Normal if QFont else 0)

    @staticmethod
    def available_arabic_fonts() -> list[str]:
        if QFontDatabase is None:
            return []
        db = QFontDatabase()
        families: set[str] = set()
        for family in db.families():
            lower = family.lower()
            if any(
                k in lower
                for k in (
                    "arabic",
                    "tahoma",
                    "traditional arabic",
                    "amiri",
                    "noto naskh arabic",
                    "dubai",
                )
            ):
                families.add(family)
        return sorted(families)

    @staticmethod
    def system_arabic_font() -> str:
        preferred = [
            "Segoe UI",
            "Tahoma",
            "Traditional Arabic",
            "Arabic Typesetting",
            "Amiri",
            "Noto Naskh Arabic",
            "Dubai",
            "Sakkal Majalla",
        ]
        if QFontDatabase is None:
            return "Segoe UI"
        db = QFontDatabase()
        for name in preferred:
            if name in db.families():
                return name
        return "Segoe UI"
