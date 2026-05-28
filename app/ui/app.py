from __future__ import annotations

from pathlib import Path
from typing import Any

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
from app.ui.dialogs.dialog_framework import DialogService
from app.ui.dialogs.notification_toast import ToastManager
from app.ui.layouts.dpi_scaling import DPIScaling
from app.ui.navigation.module_navigation import (
    ModuleDefinition,
    ModuleNavigationBuilder,
    ModuleRegistry,
    ScreenFactory,
)
from app.ui.navigation.screen_router import ScreenRegistry
from app.ui.shell.main_window import MainWindow
from app.ui.shell.splash_screen import SplashScreen
from app.ui.theme.colors import ColorScheme
from app.ui.theme.theme_manager import ThemeManager
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
from app.ui.widgets import (
    AboutScreen,
    ArchiveBrowserScreen,
    BackupCenterScreen,
    DashboardScreen,
    DiagnosticsScreen,
    LetterEditorScreen,
    RuntimeHealthScreen,
    SearchScreen,
    SettingsScreen,
    UserManagementScreen,
)

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication
except ImportError:
    QApplication = object


class UIBootstrap:
    def __init__(self, app: QApplication, container: Any | None = None) -> None:
        self._app = app
        self._container = container
        self._theme_manager = ThemeManager.get_instance()
        self._splash: SplashScreen | None = None
        self._main_window: MainWindow | None = None
        self._screen_registry = ScreenRegistry()
        self._module_registry = ModuleRegistry()
        self._screen_factory = ScreenFactory()
        self._dialog_service: DialogService | None = None
        self._toast_manager: ToastManager | None = None

    def initialize(self, font_dir: Path | None = None, rtl: bool = True) -> None:
        self._splash = SplashScreen(self._theme_manager)
        self._splash.show_message("Starting application...")
        DPIScaling.set_high_dpi_attributes()
        self._theme_manager.initialize(
            app=self._app,
            font_dir=font_dir,
            rtl=rtl or self._theme_manager.detect_rtl_from_locale(),
            scheme=ColorScheme.LIGHT,
        )
        self._app.setStyleSheet(self._theme_manager.get_stylesheet())
        if rtl:
            self._app.setLayoutDirection(Qt.RightToLeft)
        self._register_modules()
        self._register_screen_factories()
        router = self._build_router()
        self._main_window = MainWindow(router, self._theme_manager)
        self._dialog_service = DialogService(self._main_window)
        self._toast_manager = ToastManager(self._main_window)
        self._splash.close()
        self._main_window.show()

    def _register_modules(self) -> None:
        modules = [
            ModuleDefinition("dashboard", "Dashboard", "📊", "main", 0),
            ModuleDefinition("letter_editor", "Letter Editor", "✉", "main", 1),
            ModuleDefinition("archive_browser", "Archive Browser", "📁", "main", 2),
            ModuleDefinition("search", "Search", "🔍", "main", 3),
            ModuleDefinition("user_management", "User Management", "👥", "admin", 4),
            ModuleDefinition("backup_center", "Backup Center", "💾", "admin", 5),
            ModuleDefinition("settings", "Settings", "⚙", "admin", 6),
            ModuleDefinition("diagnostics", "Diagnostics", "🔬", "system", 7),
            ModuleDefinition("runtime_health", "Runtime Health", "❤", "system", 8),
            ModuleDefinition("about", "About", "ℹ", "system", 9),
        ]
        for m in modules:
            self._module_registry.register(m)

    def _register_screen_factories(self) -> None:
        factories = {
            "dashboard": lambda: self._create_screen(
                DashboardViewModel, DashboardController, DashboardScreen
            ),
            "letter_editor": lambda: self._create_screen(
                LetterEditorViewModel, LetterEditorController, LetterEditorScreen
            ),
            "archive_browser": lambda: self._create_screen(
                ArchiveBrowserViewModel, ArchiveBrowserController, ArchiveBrowserScreen
            ),
            "search": lambda: self._create_screen(SearchViewModel, SearchController, SearchScreen),
            "user_management": lambda: self._create_screen(
                UserManagementViewModel, UserManagementController, UserManagementScreen
            ),
            "backup_center": lambda: self._create_screen(
                BackupViewModel, BackupController, BackupCenterScreen
            ),
            "settings": lambda: self._create_screen(
                SettingsViewModel, SettingsController, SettingsScreen
            ),
            "diagnostics": lambda: self._create_screen(
                DiagnosticsViewModel, DiagnosticsController, DiagnosticsScreen
            ),
            "runtime_health": lambda: self._create_screen(
                RuntimeHealthViewModel, RuntimeHealthController, RuntimeHealthScreen
            ),
            "about": lambda: self._create_screen(AboutViewModel, AboutController, AboutScreen),
        }
        for sid, factory in factories.items():
            self._screen_factory.register_factory(sid, factory)

    def _create_screen(self, vm_cls, ctrl_cls, widget_cls) -> tuple:
        vm = vm_cls()
        ctrl = ctrl_cls(vm)
        widget = widget_cls(vm, ctrl)
        return vm, ctrl, widget

    def _build_router(self):
        builder = ModuleNavigationBuilder(
            self._module_registry, self._screen_factory, self._screen_registry
        )
        return builder.build_screens()

    @property
    def main_window(self) -> MainWindow | None:
        return self._main_window

    @property
    def theme_manager(self) -> ThemeManager:
        return self._theme_manager

    @property
    def dialog_service(self) -> DialogService | None:
        return self._dialog_service

    @property
    def toast_manager(self) -> ToastManager | None:
        return self._toast_manager


def launch_ui(
    app: QApplication, container: Any | None = None, font_dir: Path | None = None, rtl: bool = True
) -> MainWindow:
    bootstrap = UIBootstrap(app, container)
    bootstrap.initialize(font_dir=font_dir, rtl=rtl)
    return bootstrap.main_window
