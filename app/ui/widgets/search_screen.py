from __future__ import annotations

from app.ui.controllers.screen_controllers import SearchController
from app.ui.viewmodels.screen_viewmodels import SearchViewModel
from app.ui.widgets.page_container import PageContainer

try:
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
except ImportError:
    QWidget = object


class SearchScreen(QWidget):
    def __init__(self, view_model: SearchViewModel, controller: SearchController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        container = PageContainer("search", "Search", "Search across all correspondence")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.addWidget(QLabel("Search interface will be rendered here"))
        cl.addStretch(1)
        container.set_content(content)
