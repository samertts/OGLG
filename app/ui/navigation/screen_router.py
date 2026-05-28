from __future__ import annotations

from dataclasses import dataclass

from loguru import logger

from app.ui.controllers.base_controller import BaseController
from app.ui.viewmodels.base_viewmodel import ScreenViewModel

try:
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtWidgets import QWidget
except ImportError:
    QObject = object
    Signal = object


@dataclass
class ScreenEntry:
    id: str
    view_model: ScreenViewModel
    controller: BaseController
    widget: QWidget
    title: str
    icon_name: str = ""
    category: str = "main"
    order: int = 0
    lazy_loaded: bool = False


class ScreenRegistry:
    def __init__(self) -> None:
        self._screens: dict[str, ScreenEntry] = {}

    def register(self, entry: ScreenEntry) -> None:
        if entry.id in self._screens:
            raise ValueError(f"Screen already registered: {entry.id}")
        self._screens[entry.id] = entry
        logger.debug(f"Screen registered: {entry.id}")

    def get(self, screen_id: str) -> ScreenEntry | None:
        return self._screens.get(screen_id)

    @property
    def screens(self) -> list[ScreenEntry]:
        return sorted(self._screens.values(), key=lambda s: s.order)

    @property
    def screen_ids(self) -> list[str]:
        return [s.id for s in self.screens]

    def __contains__(self, screen_id: str) -> bool:
        return screen_id in self._screens


class ScreenRouter(QObject):
    screen_changed = Signal(str)
    navigation_failed = Signal(str, str)

    def __init__(self, registry: ScreenRegistry) -> None:
        super().__init__()
        self._registry = registry
        self._current_id: str | None = None
        self._history: list[str] = []
        self._max_history = 20

    @property
    def registry(self) -> ScreenRegistry:
        return self._registry

    @property
    def current_id(self) -> str | None:
        return self._current_id

    @property
    def current_screen(self) -> ScreenEntry | None:
        if self._current_id is None:
            return None
        return self._registry.get(self._current_id)

    @property
    def history(self) -> list[str]:
        return list(self._history)

    @property
    def screens(self) -> list[ScreenEntry]:
        return self._registry.screens

    def navigate_to(self, screen_id: str) -> bool:
        screen = self._registry.get(screen_id)
        if screen is None:
            logger.warning(f"Screen not found: {screen_id}")
            self.navigation_failed.emit(screen_id, "Screen not found")
            return False
        if screen_id == self._current_id:
            return True
        try:
            if not screen.controller.initialized:
                screen.controller.initialize()
            if self._current_id:
                self._history.append(self._current_id)
                if len(self._history) > self._max_history:
                    self._history.pop(0)
            self._current_id = screen_id
            self.screen_changed.emit(screen_id)
            logger.debug(f"Navigated to: {screen_id}")
            return True
        except Exception as exc:
            logger.error(f"Navigation failed: {screen_id}", extra={"error": str(exc)})
            self.navigation_failed.emit(screen_id, str(exc))
            return False

    def navigate_back(self) -> bool:
        if not self._history:
            return False
        previous_id = self._history.pop()
        return self.navigate_to(previous_id)

    def navigate_home(self) -> bool:
        screens = self._registry.screens
        if screens:
            return self.navigate_to(screens[0].id)
        return False

    def current_nav_path(self) -> list[str]:
        path = list(self._history)
        if self._current_id:
            path.append(self._current_id)
        return path

    def shutdown(self) -> None:
        for screen in self._registry.screens:
            try:
                if screen.controller.initialized:
                    screen.controller.dispose()
            except Exception as exc:
                logger.warning(f"Error disposing screen {screen.id}", extra={"error": str(exc)})
        logger.info("ScreenRouter shutdown complete")
