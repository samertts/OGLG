from __future__ import annotations

from pathlib import Path

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPixmap
    from PySide6.QtWidgets import (
        QDialog,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QScrollArea,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    QWidget = object


class AttachmentPreviewShell(QDialog):
    SUPPORTED_IMAGE = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}
    SUPPORTED_TEXT = {".txt", ".csv", ".log", ".md", ".xml", ".json", ".html", ".htm"}

    def __init__(self, file_path: Path | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._file_path = file_path
        self._content_area: QScrollArea | None = None
        self._content_label: QLabel | None = None
        self._info_label: QLabel | None = None
        self._setup_ui()
        if file_path:
            self.load_file(file_path)

    def _setup_ui(self) -> None:
        self.setWindowTitle("Attachment Preview")
        self.setMinimumSize(600, 500)
        layout = QVBoxLayout(self)

        self._info_label = QLabel()
        self._info_label.setStyleSheet("color: #757575; padding: 8px;")
        layout.addWidget(self._info_label)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._content_label = QLabel()
        self._content_label.setAlignment(Qt.AlignCenter)
        self._content_label.setWordWrap(True)
        self._scroll.setWidget(self._content_label)
        layout.addWidget(self._scroll, 1)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn, 0, Qt.AlignRight)

    def load_file(self, file_path: Path) -> None:
        self._file_path = file_path
        ext = file_path.suffix.lower()
        self._info_label.setText(f"File: {file_path.name}")
        if ext in self.SUPPORTED_IMAGE:
            self._load_image(file_path)
        elif ext in self.SUPPORTED_TEXT:
            self._load_text(file_path)
        else:
            self._content_label.setText(
                f"Preview not available for {ext} files.\nFile: {file_path.name}"
            )

    def _load_image(self, path: Path) -> None:
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            self._content_label.setText("Failed to load image")
            return
        max_size = 800
        if pixmap.width() > max_size or pixmap.height() > max_size:
            pixmap = pixmap.scaled(max_size, max_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._content_label.setPixmap(pixmap)

    def _load_text(self, path: Path) -> None:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            self._content_label.setText(text)
            self._content_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        except Exception as exc:
            self._content_label.setText(f"Error reading file: {exc}")
