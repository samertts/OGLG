from __future__ import annotations

from app.ui.controllers.screen_controllers import UserManagementController
from app.ui.viewmodels.screen_viewmodels import UserManagementViewModel
from app.ui.widgets.page_container import PageContainer

try:
    from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
except ImportError:
    QWidget = object


class UserManagementScreen(QWidget):
    def __init__(self, view_model: UserManagementViewModel, controller: UserManagementController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        container = PageContainer("user_management", "User Management", "Manage system users and permissions")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.addWidget(QLabel("User management interface will be rendered here"))
        cl.addStretch(1)
        container.set_content(content)
