from __future__ import annotations

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSizePolicy,
        QToolButton,
        QWidget,
    )
except ImportError:
    QWidget = object


class HeaderToolbar(QWidget):
    menu_clicked = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title_label: QLabel | None = None
        self._action_buttons: dict[str, QToolButton] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setObjectName("HeaderToolbar")
        self.setFixedHeight(56)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)

        self._title_label = QLabel("نظام المراسلات الحكومية")
        self._title_label.setObjectName("HeaderTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self._title_label.setFont(font)
        layout.addWidget(self._title_label)

        layout.addStretch(1)

        self.setLayout(layout)

    def set_title(self, title: str) -> None:
        if self._title_label:
            self._title_label.setText(title)

    def add_action_button(self, action_id: str, text: str) -> QToolButton:
        btn = QToolButton()
        btn.setText(text)
        btn.setObjectName(f"HeaderAction_{action_id}")
        btn.clicked.connect(lambda: self.menu_clicked.emit(action_id))
        self._action_buttons[action_id] = btn
        self.layout().addWidget(btn)
        return btn

    def remove_action_button(self, action_id: str) -> None:
        btn = self._action_buttons.pop(action_id, None)
        if btn:
            self.layout().removeWidget(btn)
            btn.deleteLater()
