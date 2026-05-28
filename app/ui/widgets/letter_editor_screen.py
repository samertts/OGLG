from __future__ import annotations

from app.ui.controllers.screen_controllers import LetterEditorController
from app.ui.viewmodels.screen_viewmodels import LetterEditorViewModel
from app.ui.widgets.page_container import PageContainer

try:
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget
except ImportError:
    QWidget = object


class LetterEditorScreen(QWidget):
    def __init__(self, view_model: LetterEditorViewModel, controller: LetterEditorController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self) -> None:
        container = PageContainer("letter_editor", "Letter Editor", "Compose and edit official correspondence")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(container)

        form = QWidget()
        form_layout = QVBoxLayout(form)
        form_layout.setSpacing(12)

        rows = [
            ("Subject:", self._vm.subject.value),
            ("Recipient:", self._vm.recipient.value),
            ("Classification:", self._vm.classification.value),
        ]
        for label, val in rows:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            val_label = QLabel(val or "—")
            val_label.setStyleSheet("color: #757575;")
            row.addWidget(val_label, 1)
            form_layout.addLayout(row)
        form_layout.addStretch(1)
        container.set_content(form)
