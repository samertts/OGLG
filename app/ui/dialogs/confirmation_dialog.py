from __future__ import annotations

from app.ui.dialogs.dialog_framework import BaseDialog, DialogConfig, DialogResult

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QWidget
except ImportError:
    QWidget = object


class ConfirmationDialog(BaseDialog):
    def __init__(
        self,
        title: str,
        message: str,
        detail: str = "",
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        destructive: bool = False,
        show_detail: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        self._confirm_text = confirm_text
        self._cancel_text = cancel_text
        self._is_destructive = destructive
        config = DialogConfig(
            title=title,
            message=message,
            detail=detail,
            buttons=[confirm_text, cancel_text],
            default_button=confirm_text,
            cancel_button=cancel_text,
            show_detail_expandable=show_detail,
            min_width=420,
            max_width=520,
        )
        super().__init__(config, parent)
        self._apply_style()

    def _apply_style(self) -> None:
        if self._is_destructive:
            self.setStyleSheet("""
                QPushButton:first-of-type {
                    background-color: #D32F2F;
                    color: #FFFFFF;
                    font-weight: bold;
                }
                QPushButton:first-of-type:hover {
                    background-color: #C62828;
                }
            """ + self.styleSheet())
