from __future__ import annotations

from typing import ClassVar

from app.runtime.runtime_context import get_current_context

try:
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtGui import QColor, QFont, QPainter
    from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget
except ImportError:
    QWidget = object


class RuntimeIndicator(QFrame):
    STATE_COLORS: ClassVar[dict[str, str]] = {
        "UNINITIALIZED": "#9E9E9E",
        "INITIALIZING": "#FFB300",
        "VALIDATING": "#FFB300",
        "STARTING": "#FFB300",
        "RUNNING": "#4CAF50",
        "SHUTTING_DOWN": "#FF5722",
        "STOPPED": "#9E9E9E",
        "RECOVERING": "#FF9800",
        "FAILED": "#D32F2F",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._dot = QFrame()
        self._dot.setFixedSize(8, 8)
        self._dot.setStyleSheet(
            f"background-color: {self.STATE_COLORS['UNINITIALIZED']}; border-radius: 4px;"
        )
        self._label = QLabel("UNINITIALIZED")
        self._label.setStyleSheet("color: #616161; font-size: 11px;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(4)
        layout.addWidget(self._dot)
        layout.addWidget(self._label)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_runtime_state)
        self._timer.start(2000)

    def _poll_runtime_state(self) -> None:
        try:
            ctx = get_current_context()
            if ctx:
                state = ctx.state
            else:
                state = "UNINITIALIZED"
        except Exception:
            state = "UNINITIALIZED"
        color = self.STATE_COLORS.get(state, "#9E9E9E")
        self._dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
        self._label.setText(state)
