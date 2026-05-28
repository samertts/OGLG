from __future__ import annotations

try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget
except ImportError:
    QWidget = object


class LoadingOverlay(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._message = "Loading..."
        self._busy_count = 0
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            LoadingOverlay {
                background-color: rgba(255, 255, 255, 0.88);
            }
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(12)

        self._spinner = QLabel("⟳")
        self._spinner.setAlignment(Qt.AlignCenter)
        self._spinner.setStyleSheet("font-size: 40px; color: #1B5E20;")
        layout.addWidget(self._spinner)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setFixedWidth(180)
        self._progress.setFixedHeight(3)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 2px;
                background-color: #E0E0E0;
            }
            QProgressBar::chunk {
                background-color: #1B5E20;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self._progress, 0, Qt.AlignCenter)

        self._message_label = QLabel(self._message)
        self._message_label.setAlignment(Qt.AlignCenter)
        self._message_label.setStyleSheet("color: #424242; font-size: 13px; margin-top: 4px;")
        layout.addWidget(self._message_label)

    def show_busy(self, message: str = "Loading...") -> None:
        self._busy_count += 1
        if self._busy_count > 1:
            return
        self._message = message
        self._message_label.setText(message)
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()

    def hide_busy(self) -> None:
        self._busy_count = max(0, self._busy_count - 1)
        if self._busy_count > 0:
            return
        self.hide()

    def force_hide(self) -> None:
        self._busy_count = 0
        self.hide()

    def resizeEvent(self, event) -> None:
        if self.isVisible() and self.parent():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)

    @property
    def is_busy(self) -> bool:
        return self._busy_count > 0
