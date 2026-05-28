from __future__ import annotations

from typing import Callable

from loguru import logger

from app.ui.navigation.navigation_service import NavigationService
from app.ui.navigation.route_registry import RouteRegistry
from app.ui.navigation.screen_lifecycle import ScreenLifecycleManager

try:
    from PySide6.QtCore import QObject, Signal
    from PySide6.QtWidgets import QStackedWidget, QWidget
except ImportError:
    QObject = object
    Signal = object
    QWidget = object


class Router(QObject):
    route_changed = Signal(str, str)
    route_activated = Signal(str)
    route_deactivated = Signal(str)

    def __init__(
        self,
        registry: RouteRegistry,
        nav_service: NavigationService,
        lifecycle: ScreenLifecycleManager,
    ) -> None:
        super().__init__()
        self._registry = registry
        self._nav_service = nav_service
        self._lifecycle = lifecycle
        self._screen_widgets: dict[str, QWidget] = {}
        self._screen_factories: dict[str, Callable[[], QWidget]] = {}
        self._stack: QStackedWidget | None = None
        self._current_id: str | None = None

    @property
    def registry(self) -> RouteRegistry:
        return self._registry

    @property
    def nav_service(self) -> NavigationService:
        return self._nav_service

    @property
    def lifecycle(self) -> ScreenLifecycleManager:
        return self._lifecycle

    @property
    def current_id(self) -> str | None:
        return self._current_id

    @property
    def current_widget(self) -> QWidget | None:
        if self._current_id is None:
            return None
        return self._screen_widgets.get(self._current_id)

    @property
    def stack(self) -> QStackedWidget | None:
        return self._stack

    def set_stack(self, stack: QStackedWidget) -> None:
        self._stack = stack

    def register_screen(self, route_id: str, widget: QWidget) -> None:
        self._screen_widgets[route_id] = widget
        if self._stack is not None:
            self._stack.addWidget(widget)

    def register_factory(self, route_id: str, factory: Callable[[], QWidget]) -> None:
        self._screen_factories[route_id] = factory

    def navigate(self, route_id: str) -> bool:
        resolved = self._registry.resolve(route_id)
        route = self._registry.get(resolved)
        if route is None:
            logger.warning(f"Route not found: {route_id}")
            self._nav_service.notify_navigation_failed(route_id, "Route not found")
            return False
        if self._nav_service.is_route_blocked(resolved):
            logger.warning(f"Route blocked: {resolved}")
            self._nav_service.notify_navigation_failed(route_id, "Route blocked")
            return False
        if resolved == self._current_id:
            return True
        self._nav_service.notify_navigation_start(resolved)
        try:
            widget = self._get_or_create_widget(resolved)
            if widget is None:
                self._nav_service.notify_navigation_failed(route_id, "Widget not available")
                return False
            if self._current_id:
                self._lifecycle.mark_suspended(self._current_id)
                self.route_deactivated.emit(self._current_id)
                self._nav_service.push_history(self._current_id)
            self._current_id = resolved
            if self._stack is not None:
                self._stack.setCurrentWidget(widget)
            self._lifecycle.mark_active(resolved)
            self._nav_service.notify_navigation_complete(resolved)
            self.route_changed.emit(resolved, route.title)
            self.route_activated.emit(resolved)
            logger.debug(f"Navigated to: {resolved}")
            return True
        except Exception as exc:
            logger.error(f"Navigation error: {resolved}", extra={"error": str(exc)})
            self._nav_service.notify_navigation_failed(route_id, str(exc))
            return False

    def navigate_back(self) -> bool:
        previous = self._nav_service.pop_history()
        if previous is None:
            return False
        return self.navigate(previous)

    def navigate_home(self) -> bool:
        routes = self._registry.routes
        if routes:
            return self.navigate(routes[0].id)
        return False

    def navigate_by_index(self, index: int) -> bool:
        routes = self._registry.routes
        if 0 <= index < len(routes):
            return self.navigate(routes[index].id)
        return False

    def reload_current(self) -> None:
        if self._current_id:
            self.navigate(self._current_id)

    def _get_or_create_widget(self, route_id: str) -> QWidget | None:
        if route_id in self._screen_widgets:
            return self._screen_widgets[route_id]
        factory = self._screen_factories.get(route_id)
        if factory is None:
            return None
        widget = factory()
        self.register_screen(route_id, widget)
        return widget

    def shutdown(self) -> None:
        self._nav_service.reset()
        for route_id in list(self._screen_widgets.keys()):
            self._lifecycle.mark_disposed(route_id)
        self._screen_widgets.clear()
        logger.info("Router shutdown complete")
