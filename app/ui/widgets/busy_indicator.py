from __future__ import annotations

try:
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtGui import QColor, QFont, QPainter
    from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget
except ImportError:
    QWidget = object


class BusyOverlay(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._message = "Loading..."
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self._spinner = QLabel("⏳")
        self._spinner.setAlignment(Qt.AlignCenter)
        self._spinner.setStyleSheet("font-size: 48px;")
        layout.addWidget(self._spinner)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedWidth(200)
        self._progress.setFixedHeight(4)
        self._progress.setTextVisible(False)
        layout.addWidget(self._progress, 0, Qt.AlignCenter)

        self._message_label = QLabel(self._message)
        self._message_label.setAlignment(Qt.AlignCenter)
        self._message_label.setStyleSheet("color: #1B5E20; font-size: 14px; margin-top: 8px;")
        layout.addWidget(self._message_label)

        self.setStyleSheet("""
            BusyOverlay {
                background-color: rgba(255, 255, 255, 0.85);
                border-radius: 0px;
            }
        """)

    def show_busy(self, message: str = "Loading...") -> None:
        self._message = message
        self._message_label.setText(message)
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()

    def hide_busy(self) -> None:
        self.hide()

    def resizeEvent(self, event) -> None:
        if self.isVisible():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)
