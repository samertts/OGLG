from __future__ import annotations

from datetime import datetime, timedelta

from app.ui.viewmodels.base_viewmodel import BaseViewModel, ViewModelProperty, ViewModelState


class SessionViewModel(BaseViewModel):
    def __init__(self) -> None:
        super().__init__()
        self.session_start: ViewModelProperty[datetime | None] = ViewModelProperty(None)
        self.session_duration: ViewModelProperty[timedelta] = ViewModelProperty(timedelta())
        self.is_active: ViewModelProperty[bool] = ViewModelProperty(False)
        self.last_activity: ViewModelProperty[datetime | None] = ViewModelProperty(None)
        self.idle_minutes: ViewModelProperty[float] = ViewModelProperty(0.0)
        self.was_clean_shutdown: ViewModelProperty[bool] = ViewModelProperty(True)

    def initialize(self) -> None:
        self.state = ViewModelState.READY

    def start_session(self) -> None:
        now = datetime.now()
        self.session_start.set(now)
        self.last_activity.set(now)
        self.is_active.set(True)

    def record_activity(self) -> None:
        self.last_activity.set(datetime.now())

    def end_session(self) -> None:
        if self.session_start.value:
            self.session_duration.set(datetime.now() - self.session_start.value)
        self.is_active.set(False)
