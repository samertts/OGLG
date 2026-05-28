from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    QDialog = object


class DialogResult(Enum):
    ACCEPTED = auto()
    REJECTED = auto()
    YES = auto()
    NO = auto()
    CANCEL = auto()
    CLOSED = auto()


@dataclass
class DialogConfig:
    title: str = ""
    message: str = ""
    detail: str = ""
    informative_text: str = ""
    icon_name: str = ""
    buttons: list[str] = field(default_factory=lambda: ["OK"])
    default_button: str = "OK"
    cancel_button: str = ""
    modal: bool = True
    resizable: bool = False
    min_width: int = 400
    max_width: int = 600
    show_detail_expandable: bool = False


class DialogButton(QPushButton):
    def __init__(
        self, text: str, role: QDialogButtonBox.ButtonRole, parent: QWidget | None = None
    ) -> None:
        super().__init__(text, parent)
        self._dialog_role = role

    @property
    def dialog_role(self) -> QDialogButtonBox.ButtonRole:
        return self._dialog_role


class BaseDialog(QDialog):
    result_signal = Signal(DialogResult)

    def __init__(self, config: DialogConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config
        self._dialog_result = DialogResult.CLOSED
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle(self._config.title)
        self.setModal(self._config.modal)
        self.setMinimumWidth(self._config.min_width)
        if not self._config.resizable:
            self.setFixedWidth(self._config.max_width)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        if self._config.message:
            msg_label = QLabel(self._config.message)
            msg_label.setWordWrap(True)
            font = QFont()
            font.setPointSize(12)
            msg_label.setFont(font)
            layout.addWidget(msg_label)

        if self._config.informative_text:
            info_label = QLabel(self._config.informative_text)
            info_label.setWordWrap(True)
            info_label.setStyleSheet("color: #757575;")
            layout.addWidget(info_label)

        if self._config.detail and self._config.show_detail_expandable:
            detail_label = QLabel(self._config.detail)
            detail_label.setWordWrap(True)
            detail_label.setStyleSheet(
                "color: #9E9E9E; font-size: 11px; padding: 8px;"
                " background: #F5F5F5; border-radius: 4px;"
            )
            layout.addWidget(detail_label)

        layout.addStretch(1)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        for btn_text in self._config.buttons:
            role = self._button_role(btn_text, self._config.default_button)
            btn = DialogButton(btn_text, role)
            btn.clicked.connect(lambda checked, b=btn_text: self._on_button_clicked(b))
            if btn_text == self._config.default_button:
                btn.setDefault(True)
                btn.setFocus()
            button_layout.addWidget(btn)
        layout.addLayout(button_layout)

    def _button_role(self, text: str, default: str) -> QDialogButtonBox.ButtonRole:
        role_map = {
            "OK": QDialogButtonBox.AcceptRole,
            "Cancel": QDialogButtonBox.RejectRole,
            "Yes": QDialogButtonBox.YesRole,
            "No": QDialogButtonBox.NoRole,
            "Close": QDialogButtonBox.RejectRole,
            "Save": QDialogButtonBox.AcceptRole,
            "Discard": QDialogButtonBox.DestructiveRole,
            "Apply": QDialogButtonBox.ApplyRole,
            "Reset": QDialogButtonBox.ResetRole,
            "Retry": QDialogButtonBox.AcceptRole,
            "Ignore": QDialogButtonBox.AcceptRole,
        }
        return role_map.get(text, QDialogButtonBox.AcceptRole)

    def _on_button_clicked(self, text: str) -> None:
        mapping = {
            "OK": DialogResult.ACCEPTED,
            "Cancel": DialogResult.CANCEL,
            "Yes": DialogResult.YES,
            "No": DialogResult.NO,
            "Close": DialogResult.CLOSED,
            "Save": DialogResult.ACCEPTED,
            "Discard": DialogResult.REJECTED,
            "Retry": DialogResult.YES,
            "Ignore": DialogResult.ACCEPTED,
            "Apply": DialogResult.ACCEPTED,
            "Reset": DialogResult.REJECTED,
        }
        self._dialog_result = mapping.get(text, DialogResult.ACCEPTED)
        self.result_signal.emit(self._dialog_result)
        self.accept() if self._dialog_result in (
            DialogResult.ACCEPTED,
            DialogResult.YES,
        ) else self.reject()

    @property
    def dialog_result(self) -> DialogResult:
        return self._dialog_result

    def closeEvent(self, event) -> None:
        self._dialog_result = DialogResult.CLOSED
        self.result_signal.emit(DialogResult.CLOSED)
        super().closeEvent(event)


class DialogService:
    _instance: DialogService | None = None

    def __init__(self, parent_widget: QWidget | None = None) -> None:
        self._parent = parent_widget

    @classmethod
    def get_instance(cls, parent: QWidget | None = None) -> DialogService:
        if cls._instance is None:
            cls._instance = cls(parent)
        return cls._instance

    def show_info(self, title: str, message: str, parent: QWidget | None = None) -> DialogResult:
        config = DialogConfig(title=title, message=message, buttons=["OK"], default_button="OK")
        dialog = BaseDialog(config, parent or self._parent)
        dialog.exec()
        return dialog.dialog_result

    def show_warning(self, title: str, message: str, parent: QWidget | None = None) -> DialogResult:
        config = DialogConfig(title=title, message=message, buttons=["OK"], default_button="OK")
        dialog = BaseDialog(config, parent or self._parent)
        dialog.exec()
        return dialog.dialog_result

    def show_error(
        self, title: str, message: str, detail: str = "", parent: QWidget | None = None
    ) -> DialogResult:
        config = DialogConfig(
            title=title,
            message=message,
            detail=detail,
            buttons=["OK"],
            default_button="OK",
            show_detail_expandable=True,
        )
        dialog = BaseDialog(config, parent or self._parent)
        dialog.exec()
        return dialog.dialog_result

    def show_confirm(
        self,
        title: str,
        message: str,
        parent: QWidget | None = None,
    ) -> DialogResult:
        config = DialogConfig(
            title=title,
            message=message,
            buttons=["Yes", "No"],
            default_button="Yes",
            cancel_button="No",
        )
        dialog = BaseDialog(config, parent or self._parent)
        dialog.exec()
        return dialog.dialog_result

    def show_yes_no_cancel(
        self,
        title: str,
        message: str,
        parent: QWidget | None = None,
    ) -> DialogResult:
        config = DialogConfig(
            title=title,
            message=message,
            buttons=["Yes", "No", "Cancel"],
            default_button="Yes",
            cancel_button="Cancel",
        )
        dialog = BaseDialog(config, parent or self._parent)
        dialog.exec()
        return dialog.dialog_result

    def show_custom(self, config: DialogConfig, parent: QWidget | None = None) -> DialogResult:
        dialog = BaseDialog(config, parent or self._parent)
        dialog.exec()
        return dialog.dialog_result
