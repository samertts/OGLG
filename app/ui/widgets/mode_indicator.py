from __future__ import annotations

from app.runtime.runtime_mode import detect_runtime_mode

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget
except ImportError:
    QWidget = object


class ModeIndicator(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(4)
        self._label = QLabel()
        self._label.setStyleSheet("color: #616161; font-size: 11px;")
        layout.addWidget(self._label)
        self._update_mode()

    def _update_mode(self) -> None:
        mode = detect_runtime_mode()
        text = mode.value.replace("_", " ").title()
        self._label.setText(f"Mode: {text}")
