from __future__ import annotations

from app.ui.controllers.base_controller import BaseController
from app.ui.viewmodels.session_viewmodel import SessionViewModel


class SessionController(BaseController):
    def __init__(self, view_model: SessionViewModel) -> None:
        super().__init__(view_model)

    @property
    def vm(self) -> SessionViewModel:
        return self._view_model

    def _on_initialize(self) -> None:
        self.vm.start_session()
        self.vm.initialize()

    def record_activity(self) -> None:
        self.vm.record_activity()

    def end_session(self) -> None:
        self.vm.end_session()
        self.vm.was_clean_shutdown.set(True)

    def mark_unclean_shutdown(self) -> None:
        self.vm.was_clean_shutdown.set(False)
