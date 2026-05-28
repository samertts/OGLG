from __future__ import annotations

from enum import Enum, auto
from typing import Callable

from loguru import logger

from app.ui.theme.theme_manager import ThemeManager

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
    from PySide6.QtWidgets import QApplication, QSplashScreen
except ImportError:
    QSplashScreen = object


class StartupStep(Enum):
    RUNTIME_CHECKS = auto()
    ENV_VALIDATION = auto()
    DEPENDENCY_CHECK = auto()
    SHELL_INIT = auto()
    THEME_LOAD = auto()
    NAV_INIT = auto()
    SCREEN_REGISTRY = auto()
    DASHBOARD_ACTIVATION = auto()
    READINESS = auto()


STARTUP_MESSAGES: dict[StartupStep, str] = {
    StartupStep.RUNTIME_CHECKS: "Checking runtime environment...",
    StartupStep.ENV_VALIDATION: "Validating system environment...",
    StartupStep.DEPENDENCY_CHECK: "Verifying dependencies...",
    StartupStep.SHELL_INIT: "Initializing shell...",
    StartupStep.THEME_LOAD: "Loading theme...",
    StartupStep.NAV_INIT: "Initializing navigation...",
    StartupStep.SCREEN_REGISTRY: "Registering screens...",
    StartupStep.DASHBOARD_ACTIVATION: "Activating dashboard...",
    StartupStep.READINESS: "Ready",
}


class StartupSplash(QSplashScreen):
    MINIMUM_MS = 1200

    def __init__(self, theme_manager: ThemeManager) -> None:
        self._theme = theme_manager
        pixmap = QPixmap(520, 360)
        pixmap.fill(Qt.transparent)
        super().__init__(pixmap)
        self._message = "Starting..."
        self._progress = 0.0
        self._steps: list[StartupStep] = []
        self._on_close_callback: Callable[[], None] | None = None

    def set_step(self, step: StartupStep) -> None:
        self._steps.append(step)
        self._message = STARTUP_MESSAGES.get(step, "Working...")
        self._progress = min(1.0, len(self._steps) / len(StartupStep))
        self.show()
        QApplication.processEvents()

    def set_on_close(self, callback: Callable[[], None]) -> None:
        self._on_close_callback = callback

    def drawContents(self, painter: QPainter) -> None:
        c = self._theme.palette
        w = self.width()
        h = self.height()

        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(0, 0, w, h, QColor(c.splash_bg))

        logo_size = 80
        logo_x = (w - logo_size) // 2
        logo_y = 48
        painter.setBrush(QColor(c.splash_fg))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(logo_x, logo_y, logo_size, logo_size, 16, 16)

        painter.setPen(QColor(c.splash_fg))
        title_font = QFont(self._theme.typography.font_family, 22, QFont.Bold)
        painter.setFont(title_font)
        painter.drawText(
            0, logo_y + logo_size + 16, w, 44, Qt.AlignCenter,
            "نظام المراسلات الحكومية",
        )

        painter.setPen(QColor(c.splash_accent))
        sub_font = QFont(self._theme.typography.font_family, 11)
        painter.setFont(sub_font)
        painter.drawText(
            0, logo_y + logo_size + 56, w, 24, Qt.AlignCenter,
            "Offline Government Correspondence System",
        )

        bar_y = h - 72
        bar_h = 4
        bar_w = w - 80
        bar_x = 40
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(c.surface_variant))
        painter.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 2, 2)
        progress_w = int(bar_w * self._progress)
        if progress_w > 0:
            painter.setBrush(QColor(c.splash_fg))
            painter.drawRoundedRect(bar_x, bar_y, progress_w, bar_h, 2, 2)

        painter.setPen(QColor(c.text_secondary))
        msg_font = QFont(self._theme.typography.font_family, 10)
        painter.setFont(msg_font)
        painter.drawText(0, bar_y + 16, w, 24, Qt.AlignCenter, self._message)

    def close(self) -> None:
        if self._on_close_callback:
            self._on_close_callback()
        QTimer.singleShot(150, super().close)
