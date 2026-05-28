from __future__ import annotations

from app.ui.controllers.base_controller import BaseController
from app.ui.viewmodels.screen_viewmodels import (
    AboutViewModel,
    ArchiveBrowserViewModel,
    BackupViewModel,
    DashboardViewModel,
    DiagnosticsViewModel,
    LetterEditorViewModel,
    RuntimeHealthViewModel,
    SearchViewModel,
    SettingsViewModel,
    UserManagementViewModel,
)


class DashboardController(BaseController):
    def __init__(self, view_model: DashboardViewModel) -> None:
        super().__init__(view_model)

    @property
    def vm(self) -> DashboardViewModel:
        return self._view_model

    def _on_initialize(self) -> None:
        self.vm.initialize()

    def refresh(self) -> None:
        self.vm.initialize()


class LetterEditorController(BaseController):
    def __init__(self, view_model: LetterEditorViewModel) -> None:
        super().__init__(view_model)

    @property
    def vm(self) -> LetterEditorViewModel:
        return self._view_model

    def _on_initialize(self) -> None:
        self.vm.initialize()

    def new_letter(self) -> None:
        self._view_model = LetterEditorViewModel()
        self._view_model.initialize()

    def save_draft(self) -> None:
        self.vm.is_draft.set(True)
        self.vm.has_unsaved_changes.set(False)

    def send_letter(self) -> None:
        self.vm.is_draft.set(False)
        self.vm.has_unsaved_changes.set(False)


class ArchiveBrowserController(BaseController):
    def __init__(self, view_model: ArchiveBrowserViewModel) -> None:
        super().__init__(view_model)

    @property
    def vm(self) -> ArchiveBrowserViewModel:
        return self._view_model

    def _on_initialize(self) -> None:
        self.vm.initialize()

    def search(self, query: str) -> None:
        self.vm.search_query.set(query)
        self.vm.initialize()

    def go_to_page(self, page: int) -> None:
        self.vm.current_page.set(page)

    def filter_by_date(self, year: int | None, month: int | None) -> None:
        self.vm.selected_year.set(year)
        self.vm.selected_month.set(month)


class SearchController(BaseController):
    def __init__(self, view_model: SearchViewModel) -> None:
        super().__init__(view_model)

    @property
    def vm(self) -> SearchViewModel:
        return self._view_model

    def _on_initialize(self) -> None:
        self.vm.initialize()

    def execute_search(self, query: str) -> None:
        self.vm.is_searching.set(True)
        self.vm.query.set(query)
        self.vm.is_searching.set(False)


class UserManagementController(BaseController):
    def __init__(self, view_model: UserManagementViewModel) -> None:
        super().__init__(view_model)

    @property
    def vm(self) -> UserManagementViewModel:
        return self._view_model

    def _on_initialize(self) -> None:
        self.vm.initialize()

    def select_user(self, user_id: str) -> None:
        self.vm.selected_user_id.set(user_id)


class BackupController(BaseController):
    def __init__(self, view_model: BackupViewModel) -> None:
        super().__init__(view_model)

    @property
    def vm(self) -> BackupViewModel:
        return self._view_model

    def _on_initialize(self) -> None:
        self.vm.initialize()

    def start_backup(self) -> None:
        self.vm.is_backing_up.set(True)
        self.vm.backup_progress.set(0.0)

    def restore_backup(self, backup_id: str) -> None:
        pass


class SettingsController(BaseController):
    def __init__(self, view_model: SettingsViewModel) -> None:
        super().__init__(view_model)

    @property
    def vm(self) -> SettingsViewModel:
        return self._view_model

    def _on_initialize(self) -> None:
        self.vm.initialize()

    def save_settings(self) -> None:
        pass

    def reset_defaults(self) -> None:
        self._view_model = SettingsViewModel()
        self._view_model.initialize()


class DiagnosticsController(BaseController):
    def __init__(self, view_model: DiagnosticsViewModel) -> None:
        super().__init__(view_model)

    @property
    def vm(self) -> DiagnosticsViewModel:
        return self._view_model

    def _on_initialize(self) -> None:
        self.vm.initialize()

    def run_diagnostics(self) -> None:
        self.vm.initialize()

    def run_specific_check(self, check_id: str) -> None:
        pass


class RuntimeHealthController(BaseController):
    def __init__(self, view_model: RuntimeHealthViewModel) -> None:
        super().__init__(view_model)

    @property
    def vm(self) -> RuntimeHealthViewModel:
        return self._view_model

    def _on_initialize(self) -> None:
        self.vm.initialize()

    def refresh_health(self) -> None:
        self.vm.initialize()


class AboutController(BaseController):
    def __init__(self, view_model: AboutViewModel) -> None:
        super().__init__(view_model)

    @property
    def vm(self) -> AboutViewModel:
        return self._view_model

    def _on_initialize(self) -> None:
        self.vm.initialize()
