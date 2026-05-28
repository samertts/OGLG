from __future__ import annotations

from typing import ClassVar

from app.ui.dialogs.dialog_framework import BaseDialog, DialogConfig, DialogResult

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QWidget
except ImportError:
    QWidget = object


class ErrorDialog(BaseDialog):
    SEVERITY_STYLES: ClassVar[dict[str, str]] = {
        "error": """
            QLabel#ErrorTitle { color: #D32F2F; font-size: 16px; font-weight: bold; }
        """,
        "warning": """
            QLabel#ErrorTitle { color: #F57F17; font-size: 16px; font-weight: bold; }
        """,
        "info": """
            QLabel#ErrorTitle { color: #1565C0; font-size: 16px; font-weight: bold; }
        """,
    }

    def __init__(
        self,
        title: str,
        message: str,
        detail: str = "",
        severity: str = "error",
        parent: QWidget | None = None,
    ) -> None:
        config = DialogConfig(
            title=title,
            message=message,
            detail=detail,
            buttons=["OK"],
            default_button="OK",
            show_detail_expandable=bool(detail),
            min_width=450,
            max_width=550,
        )
        super().__init__(config, parent)
        self._severity = severity
        self._apply_severity_style()

    def _apply_severity_style(self) -> None:
        style = self.SEVERITY_STYLES.get(self._severity, self.SEVERITY_STYLES["error"])
        self.setStyleSheet(style + self.styleSheet())

    @staticmethod
    def show_error(
        title: str,
        message: str,
        detail: str = "",
        parent: QWidget | None = None,
    ) -> DialogResult:
        dialog = ErrorDialog(title, message, detail, "error", parent)
        dialog.exec()
        return dialog.dialog_result

    @staticmethod
    def show_warning(
        title: str,
        message: str,
        detail: str = "",
        parent: QWidget | None = None,
    ) -> DialogResult:
        dialog = ErrorDialog(title, message, detail, "warning", parent)
        dialog.exec()
        return dialog.dialog_result

    @staticmethod
    def show_info(
        title: str,
        message: str,
        detail: str = "",
        parent: QWidget | None = None,
    ) -> DialogResult:
        dialog = ErrorDialog(title, message, detail, "info", parent)
        dialog.exec()
        return dialog.dialog_result
