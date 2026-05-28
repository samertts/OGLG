from __future__ import annotations

from enum import Enum, auto
from typing import ClassVar

try:
    from PySide6.QtCore import QPropertyAnimation, Qt, QTimer, Signal
    from PySide6.QtGui import QColor
    from PySide6.QtWidgets import (
        QApplication,
        QFrame,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    QWidget = object


class NotificationSeverity(Enum):
    INFO = auto()
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()


SEVERITY_STYLES: dict[NotificationSeverity, dict[str, str]] = {
    NotificationSeverity.INFO: {
        "bg": "#E3F2FD",
        "fg": "#1565C0",
        "border": "#1565C0",
        "icon": "ℹ",
    },
    NotificationSeverity.SUCCESS: {
        "bg": "#E8F5E9",
        "fg": "#2E7D32",
        "border": "#2E7D32",
        "icon": "✓",
    },
    NotificationSeverity.WARNING: {
        "bg": "#FFF3E0",
        "fg": "#E65100",
        "border": "#E65100",
        "icon": "⚠",
    },
    NotificationSeverity.ERROR: {
        "bg": "#FFEBEE",
        "fg": "#C62828",
        "border": "#C62828",
        "icon": "✕",
    },
}


class NotificationToast(QFrame):
    closed = Signal()

    def __init__(
        self,
        message: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        duration_ms: int = 4000,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._message = message
        self._severity = severity
        self._duration = duration_ms
        self._setup_ui()
        if duration_ms > 0:
            QTimer.singleShot(duration_ms, self._on_timeout)

    def _setup_ui(self) -> None:
        style = SEVERITY_STYLES[self._severity]
        self.setObjectName("NotificationToast")
        self.setStyleSheet(f"""
            #NotificationToast {{
                background-color: {style['bg']};
                border: 1px solid {style['border']};
                border-radius: 8px;
            }}
        """)
        self.setFixedWidth(360)
        self.setMinimumHeight(48)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        icon_label = QLabel(style["icon"])
        icon_label.setStyleSheet(f"color: {style['fg']}; font-size: 16px; font-weight: bold;")
        layout.addWidget(icon_label)

        msg_label = QLabel(self._message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"color: {style['fg']}; font-size: 12px;")
        layout.addWidget(msg_label, 1)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {style['fg']};
                border: none;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {style['fg']}22;
                border-radius: 10px;
            }}
        """)
        close_btn.clicked.connect(self.close_toast)
        layout.addWidget(close_btn)

    def _on_timeout(self) -> None:
        self.close_toast()

    def close_toast(self) -> None:
        self.closed.emit()
        self.close()
        self.deleteLater()


class NotificationManager(QWidget):
    _instance: NotificationManager | None = None

    MAX_VISIBLE = 5
    DISPLAY_DURATION = 4000

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        self._layout.setSpacing(8)
        self._layout.setContentsMargins(16, 16, 16, 60)
        self._active: list[NotificationToast] = []
        self._paused = False
        self.hide()

    @classmethod
    def get_instance(cls, parent: QWidget | None = None) -> NotificationManager:
        if cls._instance is None:
            cls._instance = cls(parent)
        return cls._instance

    def notify(
        self,
        message: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        duration_ms: int | None = None,
    ) -> None:
        if self._paused:
            return
        duration = duration_ms or self.DISPLAY_DURATION
        toast = NotificationToast(message, severity, duration, self)
        toast.closed.connect(lambda: self._remove_toast(toast))
        self._active.append(toast)
        self._layout.addWidget(toast)
        self._trim_excess()
        self.show()

    def _trim_excess(self) -> None:
        while len(self._active) > self.MAX_VISIBLE:
            oldest = self._active.pop(0)
            oldest.close_toast()

    def _remove_toast(self, toast: NotificationToast) -> None:
        if toast in self._active:
            self._active.remove(toast)
        if not self._active:
            self.hide()

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def clear_all(self) -> None:
        for toast in list(self._active):
            toast.close_toast()

    def info(self, message: str, duration: int | None = None) -> None:
        self.notify(message, NotificationSeverity.INFO, duration)

    def success(self, message: str, duration: int | None = None) -> None:
        self.notify(message, NotificationSeverity.SUCCESS, duration)

    def warning(self, message: str, duration: int | None = None) -> None:
        self.notify(message, NotificationSeverity.WARNING, duration)

    def error(self, message: str, duration: int | None = None) -> None:
        self.notify(message, NotificationSeverity.ERROR, duration)
