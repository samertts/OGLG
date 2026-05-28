from __future__ import annotations

from typing import ClassVar

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont, QIcon
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QSizePolicy,
        QToolButton,
        QWidget,
    )
except ImportError:
    QWidget = object


class TopToolbar(QWidget):
    menu_clicked = Signal(str)
    TOOLBAR_HEIGHT: ClassVar[int] = 56

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title_label: QLabel | None = None
        self._action_buttons: dict[str, QToolButton] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setObjectName("TopToolbar")
        self.setFixedHeight(self.TOOLBAR_HEIGHT)
        self.setStyleSheet("""
            #TopToolbar {
                background-color: #FFFFFF;
                border-bottom: 1px solid #E0E0E0;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)

        self._title_label = QLabel("نظام المراسلات الحكومية")
        self._title_label.setObjectName("TopToolbarTitle")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self._title_label.setFont(font)
        self._title_label.setStyleSheet("color: #212121;")
        layout.addWidget(self._title_label)

        layout.addStretch(1)

    def set_title(self, title: str) -> None:
        if self._title_label:
            self._title_label.setText(title)

    def add_action(self, action_id: str, text: str, icon: QIcon | None = None) -> QToolButton:
        btn = QToolButton()
        btn.setText(text)
        if icon:
            btn.setIcon(icon)
        btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        btn.setObjectName(f"TopToolbarAction_{action_id}")
        btn.clicked.connect(lambda: self.menu_clicked.emit(action_id))
        self._action_buttons[action_id] = btn
        self.layout().addWidget(btn)
        return btn

    def remove_action(self, action_id: str) -> None:
        btn = self._action_buttons.pop(action_id, None)
        if btn:
            self.layout().removeWidget(btn)
            btn.deleteLater()

    def clear_actions(self) -> None:
        for action_id in list(self._action_buttons.keys()):
            self.remove_action(action_id)
