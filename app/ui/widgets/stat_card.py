from __future__ import annotations

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget
except ImportError:
    QWidget = object


class StatCard(QFrame):
    def __init__(self, title: str, value: str, icon: str = "", parent: QWidget | None = None) -> None:
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
