from __future__ import annotations

from typing import Any

from app.ui.dialogs.confirmation_dialog import ConfirmationDialog
from app.ui.dialogs.dialog_framework import BaseDialog, DialogConfig, DialogResult
from app.ui.dialogs.error_dialog import ErrorDialog
from app.ui.dialogs.progress_dialog import ProgressDialog

try:
    from PySide6.QtWidgets import QWidget
except ImportError:
    QWidget = object


class DialogService:
    _instance: DialogService | None = None

    def __init__(self, parent: QWidget | None = None) -> None:
        self._parent = parent

    @classmethod
    def get_instance(cls, parent: QWidget | None = None) -> DialogService:
        if cls._instance is None:
            cls._instance = cls(parent)
        return cls._instance

    def info(self, title: str, message: str, parent: QWidget | None = None) -> DialogResult:
        return ErrorDialog.show_info(title, message, parent or self._parent)

    def warning(self, title: str, message: str, parent: QWidget | None = None) -> DialogResult:
        return ErrorDialog.show_warning(title, message, parent or self._parent)

    def error(
        self, title: str, message: str, detail: str = "",
        parent: QWidget | None = None,
    ) -> DialogResult:
        return ErrorDialog.show_error(title, message, detail, parent or self._parent)

    def confirm(self, title: str, message: str, parent: QWidget | None = None) -> DialogResult:
        dialog = ConfirmationDialog(title, message, parent or self._parent)
        dialog.exec()
        return dialog.dialog_result

    def confirm_destructive(
        self, title: str, message: str, confirm_text: str = "Delete",
        parent: QWidget | None = None,
    ) -> DialogResult:
        dialog = ConfirmationDialog(
            title, message, confirm_text=confirm_text,
            destructive=True, parent=parent or self._parent,
        )
        dialog.exec()
        return dialog.dialog_result

    def confirm_with_detail(
        self, title: str, message: str, detail: str,
        parent: QWidget | None = None,
    ) -> DialogResult:
        dialog = ConfirmationDialog(
            title, message, detail=detail,
            show_detail=True, parent=parent or self._parent,
        )
        dialog.exec()
        return dialog.dialog_result

    def progress(
        self, title: str, message: str, maximum: int = 100,
        parent: QWidget | None = None,
    ) -> ProgressDialog:
        dialog = ProgressDialog(title, message, maximum, parent or self._parent)
        return dialog

    def custom(self, config: DialogConfig, parent: QWidget | None = None) -> DialogResult:
        dialog = BaseDialog(config, parent or self._parent)
        dialog.exec()
        return dialog.dialog_result
