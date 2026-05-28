from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from loguru import logger

from app.ui.navigation.navigation_service import NavigationService
from app.ui.navigation.router import Router
from app.ui.navigation.sidebar import Sidebar
from app.ui.shell.startup_splash import StartupSplash
from app.ui.shell.status_bar import AppStatusBar
from app.ui.shell.top_toolbar import TopToolbar
from app.ui.theme.theme_manager import ThemeManager
from app.ui.widgets.loading_overlay import LoadingOverlay
from app.ui.widgets.mode_indicator import ModeIndicator
from app.ui.widgets.runtime_indicator import RuntimeIndicator

try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QCloseEvent, QKeySequence
    from PySide6.QtWidgets import (
        QHBoxLayout,
        QMainWindow,
        QShortcut,
        QSplitter,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    QMainWindow = object


class ShellState(Enum):
    UNINITIALIZED = auto()
    SPLASH = auto()
    INITIALIZING = auto()
    READY = auto()
    SHUTTING_DOWN = auto()
    ERROR = auto()


@dataclass
class ShellConfig:
    window_title: str = "نظام المراسلات الحكومية"
    min_width: int = 800
    min_height: int = 600
    default_width: int = 1280
    default_height: int = 800
    sidebar_expanded: bool = True
    enable_persistence: bool = True
    enable_splash: bool = True
    enable_animations: bool = True


class AppShell(QMainWindow):
    ready = Signal()
    closing = Signal()
    state_changed = Signal(ShellState)

    def __init__(
        self,
        router: Router,
        theme_manager: ThemeManager,
        config: ShellConfig | None = None,
    ) -> None:
        super().__init__()
        self._router = router
        self._theme = theme_manager
        self._config = config or ShellConfig()
        self._state = ShellState.UNINITIALIZED
        self._sidebar: Sidebar | None = None
        self._top_bar: TopToolbar | None = None
        self._status_bar: AppStatusBar | None = None
        self._loading_overlay: LoadingOverlay | None = None
        self._stack: QStackedWidget | None = None
        self._splitter: QSplitter | None = None
        self._runtime_indicator: RuntimeIndicator | None = None
        self._mode_indicator: ModeIndicator | None = None
        self._setup_ui()
        self._setup_shortcuts()
        self._connect_signals()
        self._set_state(ShellState.READY)
        logger.info("AppShell created")

    def _setup_ui(self) -> None:
        self.setWindowTitle(self._config.window_title)
        self.setMinimumSize(self._config.min_width, self._config.min_height)
        self.resize(self._config.default_width, self._config.default_height)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._top_bar = TopToolbar()
        main_layout.addWidget(self._top_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self._sidebar = Sidebar(self._router)
        body.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._router.set_stack(self._stack)
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.addWidget(self._stack)
        body.addWidget(self._splitter, 1)
        main_layout.addLayout(body, 1)

        self._loading_overlay = LoadingOverlay(self)
        self._loading_overlay.hide()

        self._status_bar = AppStatusBar(self)
        self.setStatusBar(self._status_bar)
        self._runtime_indicator = RuntimeIndicator()
        self._mode_indicator = ModeIndicator()
        self._status_bar.addPermanentWidget(self._runtime_indicator)
        self._status_bar.addPermanentWidget(self._mode_indicator)

    def _setup_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        QShortcut(QKeySequence("Ctrl+W"), self, self.close)
        QShortcut(QKeySequence("F5"), self, self._reload_current)
        QShortcut(QKeySequence("Escape"), self, self._on_escape)

    def _connect_signals(self) -> None:
        self._router.route_activated.connect(self._on_route_activated)
        self._sidebar.navigation_requested.connect(self._router.navigate)
        if self._top_bar:
            self._top_bar.menu_clicked.connect(self._on_menu_action)

    def _on_route_activated(self, route_id: str) -> None:
        route = self._router.registry.get(route_id)
        title = route.title if route else route_id
        if self._top_bar:
            self._top_bar.set_title(title)
        self._sidebar.highlight_item(route_id)
        self._status_bar.show_message(str(route_id), 3000)

    def _on_menu_action(self, action_id: str) -> None:
        self._router.navigate(action_id)

    def _reload_current(self) -> None:
        self._router.reload_current()

    def _on_escape(self) -> None:
        pass

    def show_busy(self, message: str = "Loading...") -> None:
        if self._loading_overlay:
            self._loading_overlay.show_busy(message)

    def hide_busy(self) -> None:
        if self._loading_overlay:
            self._loading_overlay.hide_busy()

    def show_status(self, message: str, timeout: int = 5000) -> None:
        if self._status_bar:
            self._status_bar.show_message(message, timeout)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._set_state(ShellState.SHUTTING_DOWN)
        self.closing.emit()
        self._router.shutdown()
        event.accept()
        logger.info("AppShell closed")

    def _set_state(self, state: ShellState) -> None:
        self._state = state
        self.state_changed.emit(state)

    @property
    def shell_state(self) -> ShellState:
        return self._state

    @property
    def router(self) -> Router:
        return self._router

    @property
    def sidebar(self) -> Sidebar | None:
        return self._sidebar

    @property
    def top_toolbar(self) -> TopToolbar | None:
        return self._top_bar

    @property
    def app_status_bar(self) -> AppStatusBar | None:
        return self._status_bar

    @property
    def is_ready(self) -> bool:
        return self._state == ShellState.READY
