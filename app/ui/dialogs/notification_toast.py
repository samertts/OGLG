from __future__ import annotations

from enum import Enum, auto
from typing import ClassVar

try:
    from PySide6.QtCore import QPoint, QPropertyAnimation, QRect, Qt, QTimer, Signal
    from PySide6.QtGui import QColor, QFont, QPainter
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


class ToastType(Enum):
    INFO = auto()
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()


class ToastNotification(QFrame):
    STYLES: ClassVar[dict[ToastType, dict[str, str]]] = {
        ToastType.INFO: {
            "bg": "#E3F2FD",
            "fg": "#1565C0",
            "icon": "ℹ",
        },
        ToastType.SUCCESS: {
            "bg": "#E8F5E9",
            "fg": "#2E7D32",
            "icon": "✓",
        },
        ToastType.WARNING: {
            "bg": "#FFF3E0",
            "fg": "#E65100",
            "icon": "⚠",
        },
        ToastType.ERROR: {
            "bg": "#FFEBEE",
            "fg": "#C62828",
            "icon": "✕",
        },
    }

    def __init__(
        self,
        message: str,
        toast_type: ToastType = ToastType.INFO,
        duration_ms: int = 3000,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._message = message
        self._toast_type = toast_type
        self._duration = duration_ms
        self._setup_ui()
        self._start_timer()

    def _setup_ui(self) -> None:
        style = self.STYLES[self._toast_type]
        self.setObjectName("ToastNotification")
        self.setStyleSheet(f"""
            #ToastNotification {{
                background-color: {style["bg"]};
                border: 1px solid {style["fg"]};
                border-radius: 8px;
            }}
        """)
        self.setFixedWidth(360)
        self.setMinimumHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        icon_label = QLabel(style["icon"])
        icon_label.setStyleSheet(f"color: {style['fg']}; font-size: 18px; font-weight: bold;")
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
                color: {style["fg"]};
                border: none;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {style["fg"]}22;
                border-radius: 10px;
            }}
        """)
        close_btn.clicked.connect(self.close_toast)
        layout.addWidget(close_btn)

    def _start_timer(self) -> None:
        if self._duration > 0:
            QTimer.singleShot(self._duration, self._fade_out)

    def _fade_out(self) -> None:
        self.close_toast()

    def close_toast(self) -> None:
        self.close()
        self.deleteLater()


class ToastManager(QWidget):
    _instance: ToastManager | None = None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")
        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        self._layout.setSpacing(8)
        self._layout.setContentsMargins(16, 16, 16, 16)
        self._active_toasts: list[ToastNotification] = []
        self.hide()

    @classmethod
    def get_instance(cls, parent: QWidget | None = None) -> ToastManager:
        if cls._instance is None:
            cls._instance = cls(parent)
        return cls._instance

    def show_toast(
        self,
        message: str,
        toast_type: ToastType = ToastType.INFO,
        duration_ms: int = 3000,
    ) -> None:
        toast = ToastNotification(message, toast_type, duration_ms, self)
        self._active_toasts.append(toast)
        self._layout.addWidget(toast)
        self.show()
        toast.destroyed.connect(lambda: self._on_toast_closed(toast))

    def _on_toast_closed(self, toast: ToastNotification) -> None:
        if toast in self._active_toasts:
            self._active_toasts.remove(toast)
        if not self._active_toasts:
            self.hide()

    def show_info(self, message: str, duration: int = 3000) -> None:
        self.show_toast(message, ToastType.INFO, duration)

    def show_success(self, message: str, duration: int = 3000) -> None:
        self.show_toast(message, ToastType.SUCCESS, duration)

    def show_warning(self, message: str, duration: int = 4000) -> None:
        self.show_toast(message, ToastType.WARNING, duration)

    def show_error(self, message: str, duration: int = 5000) -> None:
        self.show_toast(message, ToastType.ERROR, duration)

    def clear_all(self) -> None:
        for toast in list(self._active_toasts):
            toast.close_toast()
