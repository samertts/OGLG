from __future__ import annotations

from app.ui.controllers.screen_controllers import AboutController
from app.ui.viewmodels.screen_viewmodels import AboutViewModel
from app.ui.widgets.page_container import PageContainer

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget
except ImportError:
    QWidget = object


class AboutScreen(QWidget):
    def __init__(self, view_model: AboutViewModel, controller: AboutController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        container = PageContainer("about", "About", f"Version {self._vm.version.value}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        content = QWidget()
        cl = QVBoxLayout(content)
        info_group = QGroupBox("Version Information")
        info_layout = QVBoxLayout(info_group)
        fields = [
            ("Version:", self._vm.version.value),
            ("Python:", self._vm.python_version.value),
            ("Qt:", self._vm.qt_version.value),
            ("Organization:", self._vm.organization.value),
        ]
        for label_text, val in fields:
            row = QHBoxLayout()
            row.addWidget(QLabel(label_text))
            val_label = QLabel(str(val))
            val_label.setStyleSheet("color: #757575;")
            row.addWidget(val_label, 1)
            info_layout.addLayout(row)
        cl.addWidget(info_group)
        cl.addStretch(1)
        container.set_content(content)
