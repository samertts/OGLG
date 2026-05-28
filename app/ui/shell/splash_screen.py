from __future__ import annotations

from app.ui.theme.theme_manager import ThemeManager

try:
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
    from PySide6.QtWidgets import QApplication, QSplashScreen, QWidget
except ImportError:
    QSplashScreen = object


class SplashScreen(QSplashScreen):
    MINIMUM_MS = 1500

    def __init__(self, theme_manager: ThemeManager) -> None:
        self._theme = theme_manager
        pixmap = QPixmap(480, 320)
        pixmap.fill(Qt.transparent)
        super().__init__(pixmap)
        self._message = ""
        self._progress = 0.0
        self._elapsed = 0

    def show_message(self, message: str) -> None:
        self._message = message
        self.show()
        QApplication.processEvents()

    def set_progress(self, value: float) -> None:
        self._progress = max(0.0, min(1.0, value))
        self.show()
        QApplication.processEvents()

    def drawContents(self, painter: QPainter) -> None:
        c = self._theme.palette
        s = self._theme.spacing
        w = self.width()
        h = self.height()

        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(0, 0, w, h, QColor(c.splash_bg))

        logo_size = s.splash_logo_size
        logo_x = (w - logo_size) // 2
        logo_y = 40
        painter.setBrush(QColor(c.splash_fg))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(logo_x, logo_y, logo_size, logo_size, 16, 16)

        painter.setPen(QColor(c.splash_fg))
        title_font = QFont(self._theme.typography.font_family, 20, QFont.Bold)
        painter.setFont(title_font)
        title = "نظام المراسلات الحكومية"
        painter.drawText(0, logo_y + logo_size + 16, w, 40, Qt.AlignCenter, title)

        painter.setPen(QColor(c.splash_accent))
        sub_font = QFont(self._theme.typography.font_family, 12)
        painter.setFont(sub_font)
        painter.drawText(
            0,
            logo_y + logo_size + 52,
            w,
            30,
            Qt.AlignCenter,
            "Offline Government Correspondence System",
        )

        bar_y = h - 80
        bar_h = s.splash_progress_height
        bar_w = w - 2 * s.splash_text_margin
        bar_x = s.splash_text_margin
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(c.surface_variant))
        painter.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 2, 2)
        progress_w = int(bar_w * self._progress)
        if progress_w > 0:
            painter.setBrush(QColor(c.splash_fg))
            painter.drawRoundedRect(bar_x, bar_y, progress_w, bar_h, 2, 2)

        if self._message:
            painter.setPen(QColor(c.text_secondary))
            msg_font = QFont(self._theme.typography.font_family, 10)
            painter.setFont(msg_font)
            painter.drawText(0, bar_y + 16, w, 24, Qt.AlignCenter, self._message)

    def close(self) -> None:
        QTimer.singleShot(200, super().close)
