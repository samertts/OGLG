from __future__ import annotations

from app.ui.navigation.screen_router import ScreenEntry, ScreenRouter

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    QWidget = object


class SidebarItem(QWidget):
    clicked = Signal(str)

    def __init__(self, screen_entry: ScreenEntry, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._entry = screen_entry
        self._selected = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        self._icon_label = QLabel(self._entry.icon_name or "•")
        self._icon_label.setFixedSize(24, 24)
        self._icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._icon_label)

        self._title_label = QLabel(self._entry.title)
        self._title_label.setObjectName("SidebarItemTitle")
        layout.addWidget(self._title_label, 1)

        self.setFixedHeight(48)
        self._update_style()

    def _update_style(self) -> None:
        if self._selected:
            self.setStyleSheet("""
                SidebarItem {
                    background-color: #F57F17;
                    border-radius: 0px;
                }
                QLabel { color: #FFFFFF; font-weight: bold; }
            """)
        else:
            self.setStyleSheet("""
                SidebarItem {
                    background-color: transparent;
                    border-radius: 0px;
                }
                SidebarItem:hover {
                    background-color: #4C8C4A;
                }
                QLabel { color: #FFFFFF; }
            """)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._update_style()

    @property
    def screen_id(self) -> str:
        return self._entry.id

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self._entry.id)
        super().mousePressEvent(event)


class Sidebar(QWidget):
    navigation_requested = Signal(str)
    COLLAPSED_WIDTH = 56
    EXPANDED_WIDTH = 240

    def __init__(self, screen_router: ScreenRouter, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._router = screen_router
        self._collapsed = False
        self._items: dict[str, SidebarItem] = {}
        self._selected_id: str | None = None
        self._setup_ui()
        self._populate_items()

    def _setup_ui(self) -> None:
        self.setObjectName("AppSidebar")
        self.setFixedWidth(self.EXPANDED_WIDTH)
        self.setStyleSheet("""
            #AppSidebar {
                background-color: #1B5E20;
                border-right: 1px solid #003300;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._items_container = QVBoxLayout()
        self._items_container.setContentsMargins(0, 8, 0, 0)
        self._items_container.setSpacing(2)
        layout.addLayout(self._items_container)
        layout.addStretch(1)

    def _populate_items(self) -> None:
        categories: dict[str, list[ScreenEntry]] = {}
        for screen in self._router.screens:
            cat = screen.category or "main"
            categories.setdefault(cat, []).append(screen)

        for cat, entries in categories.items():
            for entry in entries:
                item = SidebarItem(entry)
                item.clicked.connect(self._on_item_clicked)
                self._items[entry.id] = item
                self._items_container.addWidget(item)

    def _on_item_clicked(self, screen_id: str) -> None:
        self.highlight_item(screen_id)
        self.navigation_requested.emit(screen_id)

    def highlight_item(self, screen_id: str) -> None:
        if self._selected_id:
            prev = self._items.get(self._selected_id)
            if prev:
                prev.set_selected(False)
        self._selected_id = screen_id
        current = self._items.get(screen_id)
        if current:
            current.set_selected(True)

    def toggle_collapse(self) -> None:
        self._collapsed = not self._collapsed
        width = self.COLLAPSED_WIDTH if self._collapsed else self.EXPANDED_WIDTH
        self.setFixedWidth(width)

    @property
    def is_collapsed(self) -> bool:
        return self._collapsed
