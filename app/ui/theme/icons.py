from __future__ import annotations

from enum import Enum, auto
from pathlib import Path
from typing import ClassVar

from loguru import logger

try:
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtGui import QColor, QIcon, QPixmap
    from PySide6.QtWidgets import QApplication, QStyle
except ImportError:
    QIcon, QPixmap = None, None
    QApplication, QStyle = None, None


class IconSize(Enum):
    TINY = auto()
    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()
    XLARGE = auto()


SIZE_MAP: dict[IconSize, int] = {
    IconSize.TINY: 12,
    IconSize.SMALL: 16,
    IconSize.MEDIUM: 24,
    IconSize.LARGE: 32,
    IconSize.XLARGE: 48,
}

BUILTIN_ICONS: dict[str, str] = {
    "dashboard": "📊",
    "letter": "✉",
    "archive": "📁",
    "search": "🔍",
    "users": "👥",
    "backup": "💾",
    "settings": "⚙",
    "diagnostics": "🔬",
    "health": "❤",
    "about": "ℹ",
    "home": "🏠",
    "back": "◀",
    "forward": "▶",
    "add": "➕",
    "edit": "✏",
    "delete": "🗑",
    "save": "💾",
    "print": "🖨",
    "export": "📤",
    "import": "📥",
    "refresh": "🔄",
    "close": "✕",
    "menu": "☰",
    "help": "❓",
    "warning": "⚠",
    "error": "✕",
    "success": "✓",
    "info": "ℹ",
    "lock": "🔒",
    "unlock": "🔓",
    "filter": "🔽",
    "sort": "↕",
    "attach": "📎",
    "preview": "👁",
    "fullscreen": "⛶",
    "minimize": "─",
    "maximize": "☐",
    "restore": "⛶",
}


class Icons:
    _instance: Icons | None = None

    def __init__(self, icon_dir: Path | None = None) -> None:
        self._icon_dir = icon_dir
        self._cache: dict[str, QIcon] = {}
        self._fallback_cache: dict[str, str] = dict(BUILTIN_ICONS)

    @classmethod
    def get_instance(cls) -> Icons:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get(self, name: str, size: IconSize = IconSize.MEDIUM) -> QIcon | None:
        cache_key = f"{name}_{size.name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        icon = self._load(name, size)
        if icon is not None:
            self._cache[cache_key] = icon
        return icon

    def get_text(self, name: str) -> str:
        return self._fallback_cache.get(name, "•")

    def _load(self, name: str, size: IconSize) -> QIcon | None:
        if QIcon is None:
            return None
        px_size = SIZE_MAP[size]
        if self._icon_dir:
            for ext in (".svg", ".png", ".ico"):
                path = self._icon_dir / f"{name}{ext}"
                if path.exists():
                    return QIcon(str(path))
                path_dark = self._icon_dir / f"{name}_dark{ext}"
                if path_dark.exists():
                    return QIcon(str(path_dark))
        return self._fallback_pixmap(name, px_size)

    def _fallback_pixmap(self, name: str, px_size: int) -> QIcon | None:
        if QPixmap is None:
            return None
        text = self._fallback_cache.get(name, "•")
        pixmap = QPixmap(px_size, px_size)
        pixmap.fill(Qt.transparent)
        from PySide6.QtGui import QPainter, QFont
        painter = QPainter(pixmap)
        font = QFont("Segoe UI Emoji", px_size // 2)
        painter.setFont(font)
        painter.setPen(QColor("#1B5E20"))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        painter.end()
        return QIcon(pixmap)

    def get_standard(self, standard_pixmap: int, size: IconSize = IconSize.MEDIUM) -> QIcon | None:
        if QApplication is None or QStyle is None:
            return None
        style = QApplication.style()
        icon = style.standardIcon(standard_pixmap)
        return icon

    def clear_cache(self) -> None:
        self._cache.clear()

    def mirror_for_rtl(self, icon: QIcon) -> QIcon | None:
        if QPixmap is None or icon is None:
            return icon
        from PySide6.QtGui import QTransform
        pixmap = icon.pixmap(24, 24)
        mirrored = pixmap.transformed(QTransform().scale(-1, 1))
        return QIcon(mirrored)
