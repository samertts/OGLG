from __future__ import annotations

from app.ui.controllers.screen_controllers import DiagnosticsController
from app.ui.viewmodels.screen_viewmodels import DiagnosticsViewModel
from app.ui.widgets.page_container import PageContainer

try:
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
except ImportError:
    QWidget = object


class DiagnosticsScreen(QWidget):
    def __init__(self, view_model: DiagnosticsViewModel, controller: DiagnosticsController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        container = PageContainer("diagnostics", "Diagnostics", "System diagnostics and health checks")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.addWidget(QLabel("Diagnostics interface will be rendered here"))
        cl.addStretch(1)
        container.set_content(content)
