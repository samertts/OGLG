from __future__ import annotations

from app.ui.controllers.screen_controllers import DashboardController
from app.ui.viewmodels.screen_viewmodels import DashboardViewModel
from app.ui.widgets.page_container import PageContainer
from app.ui.widgets.stat_card import StatCard

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QVBoxLayout, QWidget
except ImportError:
    QWidget = object


class DashboardScreen(QWidget):
    def __init__(self, view_model: DashboardViewModel, controller: DashboardController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._cards: dict[str, StatCard] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        container = PageContainer("dashboard", "Dashboard", "System overview and recent activity")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

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

        content = QWidget()
        content.setLayout(cards_grid)
        container.set_content(content)

        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: #2E7D32; font-size: 14px;")
        status_layout.addWidget(self._status_label)
        container.layout().addWidget(status_group)
        container.layout().addStretch(1)
