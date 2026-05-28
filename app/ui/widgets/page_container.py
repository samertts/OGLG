from __future__ import annotations

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
except ImportError:
    QWidget = object


class PageHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16)

        self._title = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        self._title.setFont(title_font)
        self._title.setStyleSheet("color: #212121;")
        layout.addWidget(self._title)

        if subtitle:
            self._subtitle = QLabel(subtitle)
            self._subtitle.setStyleSheet("color: #757575; font-size: 13px; margin-top: 2px;")
            layout.addWidget(self._subtitle)

    def set_title(self, title: str) -> None:
        self._title.setText(title)

    def set_subtitle(self, subtitle: str) -> None:
        if hasattr(self, "_subtitle"):
            self._subtitle.setText(subtitle)


class PageContainer(QWidget):
    def __init__(self, screen_id: str, title: str, subtitle: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._screen_id = screen_id
        self._header: PageHeader | None = None
        self._content: QWidget | None = None
        self._setup_ui(title, subtitle)

    def _setup_ui(self, title: str, subtitle: str) -> None:
        self.setObjectName(f"PageContainer_{self._screen_id}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        self._header = PageHeader(title, subtitle)
        layout.addWidget(self._header)

        self._content_area = QVBoxLayout()
        self._content_area.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self._content_area, 1)

    def set_content(self, widget: QWidget) -> None:
        if self._content:
            self._content_area.removeWidget(self._content)
            self._content.deleteLater()
        self._content = widget
        self._content_area.addWidget(widget)

    def set_header_visible(self, visible: bool) -> None:
        if self._header:
            self._header.setVisible(visible)

    def set_title(self, title: str) -> None:
        if self._header:
            self._header.set_title(title)

    @property
    def screen_id(self) -> str:
        return self._screen_id
