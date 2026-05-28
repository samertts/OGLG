from __future__ import annotations

from enum import Enum, auto
from pathlib import Path
from typing import ClassVar

from loguru import logger

try:
    from PySide6.QtCore import QDir, QSize, Qt
    from PySide6.QtGui import QColor, QIcon, QPixmap
    from PySide6.QtWidgets import QApplication, QStyle
except ImportError:
    QIcon, QPixmap = None, None
    QApplication, QStyle = None, None


class IconSize(Enum):
    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()
    XLARGE = auto()


class IconStrategy:
    FALLBACK_COLOR: ClassVar[str] = "#1B5E20"
    SIZE_MAP: ClassVar[dict[IconSize, int]] = {
        IconSize.SMALL: 16,
        IconSize.MEDIUM: 24,
        IconSize.LARGE: 32,
        IconSize.XLARGE: 48,
    }

    _instance: IconStrategy | None = None

    def __init__(self, icon_dir: Path | None = None) -> None:
        self._icon_dir = icon_dir
        self._cache: dict[str, QIcon] = {}
        self._svg_cache: dict[str, bytes] = {}
        logger.debug("IconStrategy initialized")

    @classmethod
    def get_instance(cls) -> IconStrategy:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_icon(self, name: str, size: IconSize = IconSize.MEDIUM) -> QIcon | None:
        cache_key = f"{name}_{size.name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        icon = self._load_icon(name, size)
        if icon is not None:
            self._cache[cache_key] = icon
        return icon

    def get_standard_icon(
        self,
        standard: QStyle.StandardPixmap,
        size: IconSize = IconSize.MEDIUM,
    ) -> QIcon | None:
        if QApplication is None or QStyle is None:
            return None
        style = QApplication.style()
        icon = style.standardIcon(standard)
        return icon

    def _load_icon(self, name: str, size: IconSize) -> QIcon | None:
        if QIcon is None:
            return None
        px_size = self.SIZE_MAP[size]
        if self._icon_dir:
            for ext in (".svg", ".png", ".ico"):
                for variant in ("", "_dark", "_light"):
                    path = self._icon_dir / f"{name}{variant}{ext}"
                    if path.exists():
                        icon = QIcon(str(path))
                        return icon
        return self._fallback_icon(name, px_size)

    def _fallback_icon(self, name: str, px_size: int) -> QIcon | None:
        if QPixmap is None:
            return None
        pixmap = QPixmap(px_size, px_size)
        pixmap.fill(Qt.transparent)
        from PySide6.QtGui import QPainter, QPen

        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(self.FALLBACK_COLOR), 2))
        painter.drawRect(2, 2, px_size - 4, px_size - 4)
        painter.drawLine(4, px_size // 2, px_size - 4, px_size // 2)
        painter.drawLine(px_size // 2, 4, px_size // 2, px_size - 4)
        painter.end()
        return QIcon(pixmap)

    def create_colored_icon(
        self,
        color: str,
        size: IconSize = IconSize.MEDIUM,
    ) -> QIcon | None:
        if QPixmap is None:
            return None
        px_size = self.SIZE_MAP[size]
        pixmap = QPixmap(px_size, px_size)
        pixmap.fill(Qt.transparent)
        from PySide6.QtGui import QPainter

        painter = QPainter(pixmap)
        painter.setBrush(QColor(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, px_size - 4, px_size - 4)
        painter.end()
        return QIcon(pixmap)

    def clear_cache(self) -> None:
        self._cache.clear()
        self._svg_cache.clear()

    def mirror_for_rtl(self, icon: QIcon) -> QIcon | None:
        from PySide6.QtGui import QTransform

        if QPixmap is None or icon is None:
            return icon
        pixmap = icon.pixmap(24, 24)
        mirrored = pixmap.transformed(QTransform().scale(-1, 1))
        return QIcon(mirrored)
