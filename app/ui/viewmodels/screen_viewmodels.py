from __future__ import annotations

from app.ui.viewmodels.base_viewmodel import ScreenViewModel, ViewModelProperty, ViewModelState


class DashboardViewModel(ScreenViewModel):
    def __init__(self) -> None:
        super().__init__("dashboard", "Dashboard")
        self.total_letters: ViewModelProperty[int] = ViewModelProperty(0)
        self.pending_letters: ViewModelProperty[int] = ViewModelProperty(0)
        self.draft_letters: ViewModelProperty[int] = ViewModelProperty(0)
        self.sent_today: ViewModelProperty[int] = ViewModelProperty(0)
        self.storage_used_mb: ViewModelProperty[float] = ViewModelProperty(0.0)
        self.recent_activity: ViewModelProperty[list[dict]] = ViewModelProperty([])
        self.system_status: ViewModelProperty[str] = ViewModelProperty("Checking...")

    def initialize(self) -> None:
        self.state = ViewModelState.LOADING
        self.total_letters.set(0)
        self.pending_letters.set(0)
        self.draft_letters.set(0)
        self.sent_today.set(0)
        self.storage_used_mb.set(0.0)
        self.system_status.set("Ready")
        self.state = ViewModelState.READY


class LetterEditorViewModel(ScreenViewModel):
    def __init__(self) -> None:
        super().__init__("letter_editor", "Letter Editor")
        self.letter_id: ViewModelProperty[str | None] = ViewModelProperty(None)
        self.subject: ViewModelProperty[str] = ViewModelProperty("")
        self.body: ViewModelProperty[str] = ViewModelProperty("")
        self.recipient: ViewModelProperty[str] = ViewModelProperty("")
        self.sender: ViewModelProperty[str] = ViewModelProperty("")
        self.classification: ViewModelProperty[str] = ViewModelProperty("normal")
        self.is_draft: ViewModelProperty[bool] = ViewModelProperty(True)
        self.has_unsaved_changes: ViewModelProperty[bool] = ViewModelProperty(False)
        self.attachments: ViewModelProperty[list[str]] = ViewModelProperty([])

    def initialize(self) -> None:
        self.state = ViewModelState.READY

    def mark_dirty(self) -> None:
        self.has_unsaved_changes.set(True)


class ArchiveBrowserViewModel(ScreenViewModel):
    def __init__(self) -> None:
        super().__init__("archive_browser", "Archive Browser")
        self.letters: ViewModelProperty[list[dict]] = ViewModelProperty([])
        self.search_query: ViewModelProperty[str] = ViewModelProperty("")
        self.selected_year: ViewModelProperty[int | None] = ViewModelProperty(None)
        self.selected_month: ViewModelProperty[int | None] = ViewModelProperty(None)
        self.total_count: ViewModelProperty[int] = ViewModelProperty(0)
        self.filtered_count: ViewModelProperty[int] = ViewModelProperty(0)
        self.current_page: ViewModelProperty[int] = ViewModelProperty(1)
        self.total_pages: ViewModelProperty[int] = ViewModelProperty(1)

    def initialize(self) -> None:
        self.state = ViewModelState.READY


class SearchViewModel(ScreenViewModel):
    def __init__(self) -> None:
        super().__init__("search", "Search")
        self.query: ViewModelProperty[str] = ViewModelProperty("")
        self.results: ViewModelProperty[list[dict]] = ViewModelProperty([])
        self.result_count: ViewModelProperty[int] = ViewModelProperty(0)
        self.search_type: ViewModelProperty[str] = ViewModelProperty("all")
        self.date_from: ViewModelProperty[str] = ViewModelProperty("")
        self.date_to: ViewModelProperty[str] = ViewModelProperty("")
        self.is_searching: ViewModelProperty[bool] = ViewModelProperty(False)

    def initialize(self) -> None:
        self.state = ViewModelState.READY


class UserManagementViewModel(ScreenViewModel):
    def __init__(self) -> None:
        super().__init__("user_management", "User Management")
        self.users: ViewModelProperty[list[dict]] = ViewModelProperty([])
        self.selected_user_id: ViewModelProperty[str | None] = ViewModelProperty(None)
        self.total_users: ViewModelProperty[int] = ViewModelProperty(0)
        self.active_users: ViewModelProperty[int] = ViewModelProperty(0)

    def initialize(self) -> None:
        self.state = ViewModelState.READY


class BackupViewModel(ScreenViewModel):
    def __init__(self) -> None:
        super().__init__("backup_center", "Backup Center")
        self.backups: ViewModelProperty[list[dict]] = ViewModelProperty([])
        self.last_backup: ViewModelProperty[str] = ViewModelProperty("Never")
        self.total_backups: ViewModelProperty[int] = ViewModelProperty(0)
        self.backup_size_mb: ViewModelProperty[float] = ViewModelProperty(0.0)
        self.is_backing_up: ViewModelProperty[bool] = ViewModelProperty(False)
        self.backup_progress: ViewModelProperty[float] = ViewModelProperty(0.0)

    def initialize(self) -> None:
        self.state = ViewModelState.READY


class SettingsViewModel(ScreenViewModel):
    def __init__(self) -> None:
        super().__init__("settings", "Settings")
        self.language: ViewModelProperty[str] = ViewModelProperty("ar")
        self.theme: ViewModelProperty[str] = ViewModelProperty("light")
        self.font_size: ViewModelProperty[int] = ViewModelProperty(14)
        self.auto_save: ViewModelProperty[bool] = ViewModelProperty(True)
        self.auto_save_interval: ViewModelProperty[int] = ViewModelProperty(60)
        self.confirm_before_send: ViewModelProperty[bool] = ViewModelProperty(True)
        self.backup_enabled: ViewModelProperty[bool] = ViewModelProperty(True)
        self.backup_interval_hours: ViewModelProperty[int] = ViewModelProperty(24)

    def initialize(self) -> None:
        self.state = ViewModelState.READY


class DiagnosticsViewModel(ScreenViewModel):
    def __init__(self) -> None:
        super().__init__("diagnostics", "Diagnostics")
        self.checks: ViewModelProperty[list[dict]] = ViewModelProperty([])
        self.total_checks: ViewModelProperty[int] = ViewModelProperty(0)
        self.passed_checks: ViewModelProperty[int] = ViewModelProperty(0)
        self.failed_checks: ViewModelProperty[int] = ViewModelProperty(0)
        self.overall_status: ViewModelProperty[str] = ViewModelProperty("Pending")
        self.last_run: ViewModelProperty[str] = ViewModelProperty("")

    def initialize(self) -> None:
        self.state = ViewModelState.READY


class RuntimeHealthViewModel(ScreenViewModel):
    def __init__(self) -> None:
        super().__init__("runtime_health", "Runtime Health")
        self.cpu_usage: ViewModelProperty[float] = ViewModelProperty(0.0)
        self.memory_usage_mb: ViewModelProperty[float] = ViewModelProperty(0.0)
        self.uptime_hours: ViewModelProperty[float] = ViewModelProperty(0.0)
        self.db_size_mb: ViewModelProperty[float] = ViewModelProperty(0.0)
        self.db_connections: ViewModelProperty[int] = ViewModelProperty(0)
        self.temp_dir_size_mb: ViewModelProperty[float] = ViewModelProperty(0.0)
        self.log_dir_size_mb: ViewModelProperty[float] = ViewModelProperty(0.0)
        self.status: ViewModelProperty[str] = ViewModelProperty("Healthy")

    def initialize(self) -> None:
        self.state = ViewModelState.READY


class AboutViewModel(ScreenViewModel):
    def __init__(self) -> None:
        super().__init__("about", "About")
        self.app_name: ViewModelProperty[str] = ViewModelProperty("نظام المراسلات الحكومية")
        self.version: ViewModelProperty[str] = ViewModelProperty("1.0.0")
        self.build_date: ViewModelProperty[str] = ViewModelProperty("")
        self.python_version: ViewModelProperty[str] = ViewModelProperty("")
        self.qt_version: ViewModelProperty[str] = ViewModelProperty("")
        self.db_version: ViewModelProperty[str] = ViewModelProperty("")
        self.license_info: ViewModelProperty[str] = ViewModelProperty("Proprietary")
        self.organization: ViewModelProperty[str] = ViewModelProperty("Iraqi Government")

    def initialize(self) -> None:
        import sys

        self.python_version.set(sys.version.split()[0])
        try:
            from PySide6.QtCore import __version__ as qt_ver

            self.qt_version.set(qt_ver)
        except ImportError:
            pass
        try:
            from app import __version__ as ver

            self.version.set(ver)
        except ImportError:
            pass
        self.state = ViewModelState.READY
