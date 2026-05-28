from __future__ import annotations

from typing import Any

try:
    from PySide6.QtCore import QSize, Qt, QTimer
    from PySide6.QtWidgets import QGridLayout, QLayout, QWidget
except ImportError:
    QWidget = object


class ResponsiveLayout(QGridLayout):
    BREAKPOINTS: dict[str, int] = {
        "mobile": 480,
        "tablet": 768,
        "desktop": 1024,
        "wide": 1280,
    }

    def __init__(self, parent: QWidget | None = None, columns: int = 3) -> None:
        super().__init__(parent)
        self._max_columns = columns
        self._current_columns = columns
        self._widgets: list[QWidget] = []

    def add_responsive_widget(self, widget: QWidget) -> None:
        self._widgets.append(widget)
        self._relayout()

    def remove_responsive_widget(self, widget: QWidget) -> None:
        if widget in self._widgets:
            self._widgets.remove(widget)
            self.removeWidget(widget)
        self._relayout()

    def clear_responsive(self) -> None:
        for w in self._widgets:
            self.removeWidget(w)
        self._widgets.clear()

    def resizeEvent(self, event: Any) -> None:
        self._update_columns()
        self._relayout()
        super().resizeEvent(event)

    def _update_columns(self) -> None:
        if not self.parent():
            return
        width = self.parent().width()
        if width < self.BREAKPOINTS["mobile"]:
            self._current_columns = 1
        elif width < self.BREAKPOINTS["tablet"]:
            self._current_columns = min(2, self._max_columns)
        elif width < self.BREAKPOINTS["desktop"]:
            self._current_columns = min(3, self._max_columns)
        else:
            self._current_columns = self._max_columns

    def _relayout(self) -> None:
        for w in self._widgets:
            self.removeWidget(w)
        if not self._widgets:
            return
        cols = max(1, self._current_columns)
        for i, w in enumerate(self._widgets):
            row, col = divmod(i, cols)
            self.addWidget(w, row, col)


class ResponsiveContainer(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = ResponsiveLayout(self)
        self.setLayout(self._layout)

    @property
    def responsive_layout(self) -> ResponsiveLayout:
        return self._layout
