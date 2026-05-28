from __future__ import annotations

from typing import Any

from app.ui.dialogs.dialog_framework import DialogResult

try:
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtWidgets import (
        QDialog,
        QLabel,
        QProgressBar,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    QDialog = object


class ProgressDialog(QDialog):
    cancelled = Signal()

    def __init__(
        self,
        title: str,
        message: str,
        maximum: int = 100,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 120)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self._message_label = QLabel(message)
        self._message_label.setWordWrap(True)
        layout.addWidget(self._message_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, maximum)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFixedHeight(24)
        layout.addWidget(self._progress_bar)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._on_cancel)
        layout.addWidget(self._cancel_btn, 0, Qt.AlignRight)

        self._was_cancelled = False

    def set_value(self, value: int) -> None:
        self._progress_bar.setValue(value)

    def set_message(self, message: str) -> None:
        self._message_label.setText(message)

    def set_maximum(self, maximum: int) -> None:
        self._progress_bar.setMaximum(maximum)

    def increment(self, step: int = 1) -> None:
        current = self._progress_bar.value()
        self._progress_bar.setValue(current + step)

    @property
    def value(self) -> int:
        return self._progress_bar.value()

    @property
    def was_cancelled(self) -> bool:
        return self._was_cancelled

    def _on_cancel(self) -> None:
        self._was_cancelled = True
        self.cancelled.emit()
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.setText("Cancelling...")
