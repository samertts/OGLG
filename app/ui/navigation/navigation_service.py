from __future__ import annotations

from loguru import logger

try:
    from PySide6.QtCore import QObject, Signal
except ImportError:
    QObject = object
    Signal = object


class NavigationService(QObject):
    navigation_started = Signal(str)
    navigation_completed = Signal(str)
    navigation_failed = Signal(str, str)
    navigation_history_changed = Signal(list)

    MAX_HISTORY = 50

    def __init__(self) -> None:
        super().__init__()
        self._current_route: str | None = None
        self._previous_route: str | None = None
        self._history: list[str] = []
        self._blocked_routes: set[str] = set()
        self._is_navigating = False

    @property
    def current_route(self) -> str | None:
        return self._current_route

    @property
    def previous_route(self) -> str | None:
        return self._previous_route

    @property
    def history(self) -> list[str]:
        return list(self._history)

    @property
    def is_navigating(self) -> bool:
        return self._is_navigating

    @property
    def can_go_back(self) -> bool:
        return len(self._history) > 0

    @property
    def can_go_forward(self) -> bool:
        return False

    def notify_navigation_start(self, route_id: str) -> None:
        self._is_navigating = True
        self.navigation_started.emit(route_id)
        logger.debug(f"Navigation started: {route_id}")

    def notify_navigation_complete(self, route_id: str) -> None:
        self._previous_route = self._current_route
        self._current_route = route_id
        self._is_navigating = False
        self.navigation_completed.emit(route_id)
        self.navigation_history_changed.emit(self.history)
        logger.debug(f"Navigation completed: {route_id}")

    def notify_navigation_failed(self, route_id: str, reason: str) -> None:
        self._is_navigating = False
        self.navigation_failed.emit(route_id, reason)
        logger.warning(f"Navigation failed: {route_id} - {reason}")

    def push_history(self, route_id: str) -> None:
        self._history.append(route_id)
        if len(self._history) > self.MAX_HISTORY:
            self._history.pop(0)
        self.navigation_history_changed.emit(self.history)

    def pop_history(self) -> str | None:
        if not self._history:
            return None
        route = self._history.pop()
        self.navigation_history_changed.emit(self.history)
        return route

    def clear_history(self) -> None:
        self._history.clear()
        self.navigation_history_changed.emit([])

    def block_route(self, route_id: str) -> None:
        self._blocked_routes.add(route_id)

    def unblock_route(self, route_id: str) -> None:
        self._blocked_routes.discard(route_id)

    def is_route_blocked(self, route_id: str) -> bool:
        return route_id in self._blocked_routes

    def reset(self) -> None:
        self._current_route = None
        self._previous_route = None
        self._history.clear()
        self._blocked_routes.clear()
        self._is_navigating = False

    def get_nav_path(self) -> list[str]:
        path = list(self._history)
        if self._current_route:
            path.append(self._current_route)
        return path
