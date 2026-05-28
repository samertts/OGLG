from __future__ import annotations

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
    from PySide6.QtPrintSupport import QPrinter, QPrintPreviewDialog
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    QWidget = object


class PrintPreviewShell(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._preview_widget: QTextEdit | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Print Preview")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)

        self._preview_widget = QTextEdit()
        self._preview_widget.setReadOnly(True)
        layout.addWidget(self._preview_widget)

        button_box = QDialogButtonBox()
        print_btn = button_box.addButton("Print", QDialogButtonBox.AcceptRole)
        close_btn = button_box.addButton("Close", QDialogButtonBox.RejectRole)
        print_btn.clicked.connect(self._on_print)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(button_box)

    def set_html(self, html: str) -> None:
        if self._preview_widget:
            self._preview_widget.setHtml(html)

    def set_text(self, text: str) -> None:
        if self._preview_widget:
            self._preview_widget.setPlainText(text)

    def _on_print(self) -> None:
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintPreviewDialog(printer, self)
        dialog.paintRequested.connect(self._preview_widget.print_)
        dialog.exec()
