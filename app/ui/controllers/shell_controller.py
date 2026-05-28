from __future__ import annotations

from app.ui.controllers.base_controller import BaseController
from app.ui.viewmodels.shell_viewmodel import ShellViewModel

try:
    from PySide6.QtWidgets import QWidget
except ImportError:
    QWidget = object


class ShellController(BaseController):
    def __init__(self, view_model: ShellViewModel) -> None:
        super().__init__(view_model)

    @property
    def vm(self) -> ShellViewModel:
        return self._view_model

    def _on_initialize(self) -> None:
        self.vm.initialize()

    def show_busy(self, message: str = "Loading...") -> None:
        self.vm.set_busy(message)

    def hide_busy(self) -> None:
        self.vm.clear_busy()

    def toggle_sidebar(self) -> None:
        self.vm.toggle_sidebar()

    def set_title(self, title: str) -> None:
        self.vm.set_title(title)

    def report_error(self, message: str) -> None:
        self.vm.error_message.set(message)

    def clear_error(self) -> None:
        self.vm.error_message.set(None)

    def update_startup_progress(self, step: str, progress: float) -> None:
        self.vm.startup_step.set(step)
        self.vm.startup_progress.set(progress)
