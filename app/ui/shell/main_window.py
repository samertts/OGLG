from __future__ import annotations

import json
from pathlib import Path

from loguru import logger

from app.ui.navigation.screen_router import ScreenRouter
from app.ui.navigation.sidebar import Sidebar
from app.ui.shell.header_toolbar import HeaderToolbar
from app.ui.shell.status_bar import AppStatusBar
from app.ui.theme.theme_manager import ThemeManager
from app.ui.widgets.busy_indicator import BusyOverlay
from app.ui.widgets.mode_indicator import ModeIndicator
from app.ui.widgets.runtime_indicator import RuntimeIndicator

try:
    from PySide6.QtCore import QByteArray, QSettings, QSize, Qt, Signal
    from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
    from PySide6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QMainWindow,
        QMenuBar,
        QMessageBox,
        QShortcut,
        QSplitter,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    QMainWindow = object


class MainWindow(QMainWindow):
    ready = Signal()
    screen_changed = Signal(str)

    SETTINGS_GROUP = "main_window"
    GEOMETRY_KEY = "geometry"
    STATE_KEY = "state"
    SPLITTER_KEY = "splitter"

    def __init__(
        self,
        screen_router: ScreenRouter,
        theme_manager: ThemeManager,
        window_title: str = "نظام المراسلات الحكومية",
    ) -> None:
        super().__init__()
        self._screen_router = screen_router
        self._theme_manager = theme_manager
        self._sidebar: Sidebar | None = None
        self._header: HeaderToolbar | None = None
        self._status_bar: AppStatusBar | None = None
        self._busy_overlay: BusyOverlay | None = None
        self._runtime_indicator: RuntimeIndicator | None = None
        self._mode_indicator: ModeIndicator | None = None
        self._splitter: QSplitter | None = None
        self._stack: QStackedWidget | None = None
        self._setup_ui(window_title)
        self._connect_signals()
        self._restore_window_state()
        logger.info("MainWindow created")

    def _setup_ui(self, window_title: str) -> None:
        self.setWindowTitle(window_title)
        self.setMinimumSize(800, 600)
        self.resize(1280, 800)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._header = HeaderToolbar()
        main_layout.addWidget(self._header)

        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self._sidebar = Sidebar(self._screen_router)
        body_layout.addWidget(self._sidebar)

        self._splitter = QSplitter(Qt.Horizontal)
        self._stack = QStackedWidget()
        for screen in self._screen_router.screens:
            self._stack.addWidget(screen.widget)
        self._splitter.addWidget(self._stack)
        body_layout.addWidget(self._splitter, 1)
        main_layout.addLayout(body_layout, 1)

        self._busy_overlay = BusyOverlay(self)
        self._busy_overlay.hide()

        self._status_bar = AppStatusBar(self)
        self.setStatusBar(self._status_bar)

        self._runtime_indicator = RuntimeIndicator()
        self._mode_indicator = ModeIndicator()
        self._status_bar.addPermanentWidget(self._runtime_indicator)
        self._status_bar.addPermanentWidget(self._mode_indicator)

        self._setup_keyboard_shortcuts()

    def _setup_keyboard_shortcuts(self) -> None:
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        QShortcut(QKeySequence("Ctrl+W"), self, self.close)
        QShortcut(QKeySequence("F5"), self, self._refresh_current_screen)
        QShortcut(QKeySequence("Ctrl+Shift+S"), self, self._toggle_sidebar)
        QShortcut(QKeySequence("Escape"), self, self._on_escape)

    def _connect_signals(self) -> None:
        self._screen_router.screen_changed.connect(self._on_screen_changed)
        self._sidebar.navigation_requested.connect(self._screen_router.navigate_to)

    def _on_screen_changed(self, screen_id: str) -> None:
        screen = self._screen_router.current_screen
        if screen and screen.widget:
            self._stack.setCurrentWidget(screen.widget)
            if screen.view_model:
                title = screen.view_model.title
                self._header.set_title(title)
            self._sidebar.highlight_item(screen_id)
            self._status_bar.show_message(
                f"Screen: {screen.view_model.title if screen.view_model else screen_id}",
                3000,
            )
            self.screen_changed.emit(screen_id)

    def _refresh_current_screen(self) -> None:
        screen = self._screen_router.current_screen
        if screen and screen.controller:
            screen.controller.initialize()

    def _toggle_sidebar(self) -> None:
        if self._sidebar:
            self._sidebar.toggle_collapse()

    def _on_escape(self) -> None:
        pass

    def show_busy(self, message: str = "Loading...") -> None:
        if self._busy_overlay:
            self._busy_overlay.show_busy(message)

    def hide_busy(self) -> None:
        if self._busy_overlay:
            self._busy_overlay.hide_busy()

    def show_status_message(self, message: str, timeout: int = 5000) -> None:
        if self._status_bar:
            self._status_bar.show_message(message, timeout)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._save_window_state()
        self._screen_router.shutdown()
        event.accept()
        logger.info("MainWindow closed")

    def _save_window_state(self) -> None:
        try:
            settings_path = self._get_settings_path()
            state = {
                "geometry": self.saveGeometry().toBase64().data().decode(),
                "state": self.saveState().toBase64().data().decode(),
            }
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to save window state", extra={"error": str(exc)})

    def _restore_window_state(self) -> None:
        try:
            settings_path = self._get_settings_path()
            if not settings_path.exists():
                return
            state = json.loads(settings_path.read_text(encoding="utf-8"))
            if "geometry" in state:
                geo = QByteArray.fromBase64(state["geometry"].encode())
                self.restoreGeometry(geo)
            if "state" in state:
                st = QByteArray.fromBase64(state["state"].encode())
                self.restoreState(st)
        except Exception as exc:
            logger.warning("Failed to restore window state", extra={"error": str(exc)})

    def _get_settings_path(self) -> Path:
        return Path.home() / ".oglg" / "window_state.json"

    @property
    def sidebar(self) -> Sidebar | None:
        return self._sidebar

    @property
    def header_toolbar(self) -> HeaderToolbar | None:
        return self._header

    @property
    def app_status_bar(self) -> AppStatusBar | None:
        return self._status_bar
