import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest

from app.ui.controllers.base_controller import BaseController
from app.ui.controllers.screen_controllers import (
    AboutController,
    ArchiveBrowserController,
    BackupController,
    DashboardController,
    DiagnosticsController,
    LetterEditorController,
    RuntimeHealthController,
    SearchController,
    SettingsController,
    UserManagementController,
)
from app.ui.viewmodels.base_viewmodel import BaseViewModel, ViewModelState
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


class TestBaseController:
    def test_initialization_lifecycle(self):
        class TestVM(BaseViewModel):
            def initialize(self):
                self.state = ViewModelState.READY

        class TestCtrl(BaseController):
            def _on_initialize(self):
                self._view_model.initialize()

        vm = TestVM()
        ctrl = TestCtrl(vm)
        assert not ctrl.initialized
        ctrl.initialize()
        assert ctrl.initialized
        assert ctrl.view_model.is_ready

    def test_double_initialize(self):
        class TestVM(BaseViewModel):
            called = 0

            def initialize(self):
                TestVM.called += 1

        class TestCtrl(BaseController):
            def _on_initialize(self):
                self._view_model.initialize()

        vm = TestVM()
        ctrl = TestCtrl(vm)
        ctrl.initialize()
        ctrl.initialize()
        assert TestVM.called == 1

    def test_dispose(self):
        class TestVM(BaseViewModel):
            def initialize(self):
                pass

        class TestCtrl(BaseController):
            def _on_initialize(self):
                self._view_model.initialize()

        vm = TestVM()
        ctrl = TestCtrl(vm)
        ctrl.initialize()
        ctrl.dispose()
        assert not ctrl.initialized
        assert ctrl.view_model.disposed


class TestAllControllers:
    @pytest.mark.parametrize(
        "vm_cls,ctrl_cls",
        [
            (DashboardViewModel, DashboardController),
            (LetterEditorViewModel, LetterEditorController),
            (ArchiveBrowserViewModel, ArchiveBrowserController),
            (SearchViewModel, SearchController),
            (UserManagementViewModel, UserManagementController),
            (BackupViewModel, BackupController),
            (SettingsViewModel, SettingsController),
            (DiagnosticsViewModel, DiagnosticsController),
            (RuntimeHealthViewModel, RuntimeHealthController),
            (AboutViewModel, AboutController),
        ],
    )
    def test_all_controllers_initialize(self, vm_cls, ctrl_cls):
        vm = vm_cls()
        ctrl = ctrl_cls(vm)
        assert ctrl.view_model is vm
        ctrl.initialize()
        assert ctrl.initialized

    def test_dashboard_controller_refresh(self):
        vm = DashboardViewModel()
        ctrl = DashboardController(vm)
        ctrl.initialize()
        ctrl.refresh()
        assert vm.is_ready

    def test_letter_editor_controller_new_letter(self):
        vm = LetterEditorViewModel()
        ctrl = LetterEditorController(vm)
        ctrl.initialize()
        ctrl.new_letter()
        assert ctrl.vm.screen_id == "letter_editor"

    def test_backup_controller_start_backup(self):
        vm = BackupViewModel()
        ctrl = BackupController(vm)
        ctrl.initialize()
        ctrl.start_backup()
        assert vm.is_backing_up.value

    def test_search_controller_execute(self):
        vm = SearchViewModel()
        ctrl = SearchController(vm)
        ctrl.initialize()
        ctrl.execute_search("test query")
        assert vm.query.value == "test query"
