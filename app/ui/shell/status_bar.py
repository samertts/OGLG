from __future__ import annotations

try:
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtWidgets import QLabel, QStatusBar, QWidget
except ImportError:
    QStatusBar = object


class AppStatusBar(QStatusBar):
    DEFAULT_TIMEOUT = 5000

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._message_timer = QTimer(self)
        self._message_timer.setSingleShot(True)
        self._message_timer.timeout.connect(self._clear_temporary_message)
        self._permanent_label = QLabel()
        self._temporary_label = QLabel()
        self._permanent_label.setObjectName("StatusPermanent")
        self._show_ready()

    def show_message(self, text: str, timeout: int = DEFAULT_TIMEOUT) -> None:
        self._temporary_label.setText(text)
        self.insertWidget(0, self._temporary_label)
        if timeout > 0:
            self._message_timer.start(timeout)

    def set_permanent_text(self, text: str) -> None:
        self._permanent_label.setText(text)
        self.addPermanentWidget(self._permanent_label)

    def _clear_temporary_message(self) -> None:
        self._temporary_label.clear()
        self.removeWidget(self._temporary_label)

    def _show_ready(self) -> None:
        self.show_message("Ready", 2000)

    def show_error(self, message: str) -> None:
        self._temporary_label.setStyleSheet("color: #D32F2F;")
        self.show_message(f"Error: {message}", 8000)

    def show_success(self, message: str) -> None:
        self._temporary_label.setStyleSheet("color: #2E7D32;")
        self.show_message(message, 4000)

    def show_warning(self, message: str) -> None:
        self._temporary_label.setStyleSheet("color: #F57F17;")
        self.show_message(message, 5000)
