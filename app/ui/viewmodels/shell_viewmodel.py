from __future__ import annotations

from app.ui.viewmodels.base_viewmodel import BaseViewModel, ViewModelProperty, ViewModelState


class ShellViewModel(BaseViewModel):
    def __init__(self) -> None:
        super().__init__()
        self.shell_ready: ViewModelProperty[bool] = ViewModelProperty(False)
        self.sidebar_visible: ViewModelProperty[bool] = ViewModelProperty(True)
        self.sidebar_collapsed: ViewModelProperty[bool] = ViewModelProperty(False)
        self.current_title: ViewModelProperty[str] = ViewModelProperty("نظام المراسلات الحكومية")
        self.status_message: ViewModelProperty[str] = ViewModelProperty("Ready")
        self.is_busy: ViewModelProperty[bool] = ViewModelProperty(False)
        self.busy_message: ViewModelProperty[str] = ViewModelProperty("")
        self.error_message: ViewModelProperty[str | None] = ViewModelProperty(None)
        self.theme_mode: ViewModelProperty[str] = ViewModelProperty("light")
        self.is_rtl: ViewModelProperty[bool] = ViewModelProperty(True)
        self.dpi_scale: ViewModelProperty[float] = ViewModelProperty(1.0)
        self.startup_progress: ViewModelProperty[float] = ViewModelProperty(0.0)
        self.startup_step: ViewModelProperty[str] = ViewModelProperty("")

    def initialize(self) -> None:
        self.state = ViewModelState.LOADING
        self.shell_ready.set(True)
        self.state = ViewModelState.READY

    def set_busy(self, message: str = "Loading...") -> None:
        self.is_busy.set(True)
        self.busy_message.set(message)

    def clear_busy(self) -> None:
        self.is_busy.set(False)
        self.busy_message.set("")

    def toggle_sidebar(self) -> None:
        self.sidebar_collapsed.set(not self.sidebar_collapsed.value)

    def set_title(self, title: str) -> None:
        self.current_title.set(title)
