import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest

from app.ui.viewmodels.base_viewmodel import (
    BaseViewModel,
    ScreenViewModel,
    ViewModelProperty,
    ViewModelState,
)
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


class TestViewModelProperty:
    def test_set_and_get(self):
        prop = ViewModelProperty(42)
        assert prop.value == 42
        prop.set(100)
        assert prop.value == 100

    def test_listener_called(self):
        prop = ViewModelProperty(0)
        calls = []
        prop.listen(lambda old, new: calls.append((old, new)))
        prop.set(1)
        assert calls == [(0, 1)]

    def test_no_notification_on_same_value(self):
        prop = ViewModelProperty(42)
        calls = []
        prop.listen(lambda old, new: calls.append((old, new)))
        prop.set(42)
        assert calls == []

    def test_unlisten(self):
        prop = ViewModelProperty(0)
        calls = []
        unsub = prop.listen(lambda old, new: calls.append((old, new)))
        unsub()
        prop.set(1)
        assert calls == []


class TestBaseViewModel:
    def test_initial_state(self):
        class TestVM(BaseViewModel):
            def initialize(self):
                pass

        vm = TestVM()
        assert vm.state == ViewModelState.IDLE
        assert not vm.is_loading
        assert not vm.is_ready
        assert not vm.has_error

    def test_state_transitions(self):
        class TestVM(BaseViewModel):
            def initialize(self):
                self.state = ViewModelState.LOADING
                self.state = ViewModelState.READY

        vm = TestVM()
        vm.initialize()
        assert vm.is_ready

    def test_error_state(self):
        class TestVM(BaseViewModel):
            def initialize(self):
                self.state = ViewModelState.ERROR
                self.error_message = "Something went wrong"

        vm = TestVM()
        vm.initialize()
        assert vm.has_error
        assert vm.error_message == "Something went wrong"

    def test_dispose(self):
        class TestVM(BaseViewModel):
            def initialize(self):
                pass

        vm = TestVM()
        assert not vm.disposed
        vm.dispose()
        assert vm.disposed
        vm.dispose()  # no-op


class TestScreenViewModel:
    def test_initialization(self):
        class ConcreteScreen(ScreenViewModel):
            def initialize(self):
                self.state = ViewModelState.READY

        vm = ConcreteScreen("test_screen", "Test Screen")
        assert vm.screen_id == "test_screen"
        assert vm.title == "Test Screen"

    def test_initialize_abstract(self):
        class TestScreen(ScreenViewModel):
            def initialize(self):
                self.state = ViewModelState.READY

        vm = TestScreen("test", "Test")
        vm.initialize()
        assert vm.is_ready


class TestDashboardViewModel:
    def test_initial_state(self):
        vm = DashboardViewModel()
        assert vm.screen_id == "dashboard"
        assert vm.state == ViewModelState.IDLE

    def test_initialize(self):
        vm = DashboardViewModel()
        vm.initialize()
        assert vm.is_ready
        assert vm.total_letters.value == 0


class TestLetterEditorViewModel:
    def test_initial_state(self):
        vm = LetterEditorViewModel()
        assert vm.is_draft.value is True
        assert not vm.has_unsaved_changes.value

    def test_mark_dirty(self):
        vm = LetterEditorViewModel()
        vm.mark_dirty()
        assert vm.has_unsaved_changes.value is True


class TestAboutViewModel:
    def test_initialize_sets_python_version(self):
        vm = AboutViewModel()
        vm.initialize()
        assert vm.is_ready
        assert len(vm.python_version.value) > 0


class TestAllScreenViewModels:
    @pytest.mark.parametrize(
        "vm_cls,expected_id",
        [
            (DashboardViewModel, "dashboard"),
            (LetterEditorViewModel, "letter_editor"),
            (ArchiveBrowserViewModel, "archive_browser"),
            (SearchViewModel, "search"),
            (UserManagementViewModel, "user_management"),
            (BackupViewModel, "backup_center"),
            (SettingsViewModel, "settings"),
            (DiagnosticsViewModel, "diagnostics"),
            (RuntimeHealthViewModel, "runtime_health"),
            (AboutViewModel, "about"),
        ],
    )
    def test_all_viewmodels_initialize(self, vm_cls, expected_id):
        vm = vm_cls()
        assert vm.screen_id == expected_id
        vm.initialize()
        assert vm.is_ready or vm.state == ViewModelState.READY
