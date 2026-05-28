from __future__ import annotations

from app.ui.controllers.screen_controllers import RuntimeHealthController
from app.ui.viewmodels.screen_viewmodels import RuntimeHealthViewModel
from app.ui.widgets.page_container import PageContainer

try:
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
except ImportError:
    QWidget = object


class RuntimeHealthScreen(QWidget):
    def __init__(self, view_model: RuntimeHealthViewModel, controller: RuntimeHealthController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        container = PageContainer("runtime_health", "Runtime Health", "Monitor application runtime health")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.addWidget(QLabel("Runtime health interface will be rendered here"))
        cl.addStretch(1)
        container.set_content(content)
