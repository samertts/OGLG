from __future__ import annotations

from app.ui.controllers.screen_controllers import (
    AboutController,
    ArchiveBrowserController,
    BackupController,
    DashboardController,
    DiagnosticsController,
    LetterEditorController,
    RuntimeHealthController,
    SearchController,
    SettingsController,
    UserManagementController,
)
from app.ui.viewmodels.screen_viewmodels import (
    AboutViewModel,
    ArchiveBrowserViewModel,
    BackupViewModel,
    DashboardViewModel,
    DiagnosticsViewModel,
    LetterEditorViewModel,
    RuntimeHealthViewModel,
    SearchViewModel,
    SettingsViewModel,
    UserManagementViewModel,
)

try:
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QFrame,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    QWidget = object


class StatCard(QFrame):
    def __init__(
        self, title: str, value: str, icon: str = "", parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setStyleSheet("""
            #StatCard {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 16px;
            }
            #StatCard:hover {
                border-color: #1B5E20;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 24px;")
            layout.addWidget(icon_label)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #757575; font-size: 12px;")
        layout.addWidget(title_label)
        self._value_label = QLabel(value)
        self._value_label.setStyleSheet("color: #212121; font-size: 28px; font-weight: bold;")
        layout.addWidget(self._value_label)
        self.setMinimumSize(200, 120)

    def set_value(self, value: str) -> None:
        self._value_label.setText(value)


class DashboardScreen(QWidget):
    def __init__(
        self,
        view_model: DashboardViewModel,
        controller: DashboardController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._cards: dict[str, StatCard] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #212121;")
        layout.addWidget(title)

        cards_grid = QGridLayout()
        cards_grid.setSpacing(16)
        stats = [
            ("total_letters", "Total Letters", "0"),
            ("pending", "Pending", "0"),
            ("drafts", "Drafts", "0"),
            ("sent_today", "Sent Today", "0"),
        ]
        for i, (key, title_text, default) in enumerate(stats):
            card = StatCard(title_text, default)
            self._cards[key] = card
            cards_grid.addWidget(card, i // 4, i % 4)
        layout.addLayout(cards_grid)

        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: #2E7D32; font-size: 14px;")
        status_layout.addWidget(self._status_label)
        layout.addWidget(status_group)

        layout.addStretch(1)


class LetterEditorScreen(QWidget):
    def __init__(
        self,
        view_model: LetterEditorViewModel,
        controller: LetterEditorController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Letter Editor")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #212121;")
        layout.addWidget(title)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(8)

        subject_row = QHBoxLayout()
        subject_row.addWidget(QLabel("Subject:"))
        self._subject_label = QLabel("—")
        self._subject_label.setStyleSheet("color: #757575;")
        subject_row.addWidget(self._subject_label, 1)
        form_layout.addLayout(subject_row)

        recipient_row = QHBoxLayout()
        recipient_row.addWidget(QLabel("Recipient:"))
        self._recipient_label = QLabel("—")
        recipient_row.addWidget(self._recipient_label, 1)
        form_layout.addLayout(recipient_row)

        classification_row = QHBoxLayout()
        classification_row.addWidget(QLabel("Classification:"))
        self._class_label = QLabel("normal")
        classification_row.addWidget(self._class_label, 1)
        form_layout.addLayout(classification_row)

        layout.addLayout(form_layout)
        layout.addStretch(1)


class ArchiveBrowserScreen(QWidget):
    def __init__(
        self,
        view_model: ArchiveBrowserViewModel,
        controller: ArchiveBrowserController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Archive Browser")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        info = QLabel("Browse archived correspondence")
        info.setStyleSheet("color: #757575;")
        layout.addWidget(info)
        layout.addStretch(1)


class SearchScreen(QWidget):
    def __init__(
        self,
        view_model: SearchViewModel,
        controller: SearchController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Search")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        info = QLabel("Search across all correspondence")
        info.setStyleSheet("color: #757575;")
        layout.addWidget(info)
        layout.addStretch(1)


class UserManagementScreen(QWidget):
    def __init__(
        self,
        view_model: UserManagementViewModel,
        controller: UserManagementController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("User Management")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        info = QLabel("Manage system users and permissions")
        info.setStyleSheet("color: #757575;")
        layout.addWidget(info)
        layout.addStretch(1)


class BackupCenterScreen(QWidget):
    def __init__(
        self,
        view_model: BackupViewModel,
        controller: BackupController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Backup Center")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        info = QLabel("Backup and restore system data")
        info.setStyleSheet("color: #757575;")
        layout.addWidget(info)
        layout.addStretch(1)


class SettingsScreen(QWidget):
    def __init__(
        self,
        view_model: SettingsViewModel,
        controller: SettingsController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        info = QLabel("Configure application settings")
        info.setStyleSheet("color: #757575;")
        layout.addWidget(info)
        layout.addStretch(1)


class DiagnosticsScreen(QWidget):
    def __init__(
        self,
        view_model: DiagnosticsViewModel,
        controller: DiagnosticsController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Diagnostics")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        info = QLabel("System diagnostics and checks")
        info.setStyleSheet("color: #757575;")
        layout.addWidget(info)
        layout.addStretch(1)


class RuntimeHealthScreen(QWidget):
    def __init__(
        self,
        view_model: RuntimeHealthViewModel,
        controller: RuntimeHealthController,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Runtime Health")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        info = QLabel("Monitor application runtime health")
        info.setStyleSheet("color: #757575;")
        layout.addWidget(info)
        layout.addStretch(1)


class AboutScreen(QWidget):
    def __init__(
        self, view_model: AboutViewModel, controller: AboutController, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("About نظام المراسلات الحكومية")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

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
        layout.addWidget(info_group)

        layout.addStretch(1)
