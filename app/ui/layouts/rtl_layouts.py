from __future__ import annotations

from typing import ClassVar

try:
    from PySide6.QtWidgets import (
        QFormLayout,
        QGridLayout,
        QHBoxLayout,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    QWidget = object


class RTLHBoxLayout(QHBoxLayout):
    def __init__(self, parent: QWidget | None = None, rtl: bool = False) -> None:
        super().__init__(parent)
        self._rtl = rtl
        self._update_direction()

    def set_rtl(self, enabled: bool) -> None:
        self._rtl = enabled
        self._update_direction()

    def _update_direction(self) -> None:
        self.setDirection(QHBoxLayout.RightToLeft if self._rtl else QHBoxLayout.LeftToRight)


class RTLVBoxLayout(QVBoxLayout):
    def __init__(self, parent: QWidget | None = None, rtl: bool = False) -> None:
        super().__init__(parent)
        self._rtl = rtl
        self._update_direction()

    def set_rtl(self, enabled: bool) -> None:
        self._rtl = enabled
        self._update_direction()

    def _update_direction(self) -> None:
        self.setDirection(QVBoxLayout.RightToLeft if self._rtl else QVBoxLayout.LeftToRight)


class RTLFormLayout(QFormLayout):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def add_row_rtl(self, label: str, field: QWidget) -> None:
        self.addRow(field, None)
        self.setWidget(0, QFormLayout.LabelRole, None)


class RTLGridLayout(QGridLayout):
    def __init__(self, parent: QWidget | None = None, rtl: bool = False) -> None:
        super().__init__(parent)
        self._rtl = rtl
        self._update_alignment()

    def set_rtl(self, enabled: bool) -> None:
        self._rtl = enabled
        self._update_alignment()

    def _update_alignment(self) -> None:
        pass


class SpacerHelper:
    H_SPACER_SIZES: ClassVar[dict[str, int]] = {
        "xs": 4,
        "sm": 8,
        "md": 16,
        "lg": 24,
        "xl": 32,
    }
    V_SPACER_SIZES: ClassVar[dict[str, int]] = {
        "xs": 4,
        "sm": 8,
        "md": 16,
        "lg": 24,
        "xl": 32,
    }

    @staticmethod
    def h_spacer(size: str = "md") -> QWidget:
        w = QWidget()
        w.setFixedWidth(SpacerHelper.H_SPACER_SIZES.get(size, 16))
        return w

    @staticmethod
    def v_spacer(size: str = "md") -> QWidget:
        w = QWidget()
        w.setFixedHeight(SpacerHelper.V_SPACER_SIZES.get(size, 16))
        return w
