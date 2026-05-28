from __future__ import annotations

from typing import Callable

from app.ui.controllers.base_controller import BaseController
from app.ui.navigation.router import Router
from app.ui.viewmodels.navigation_viewmodel import NavigationViewModel


class NavigationController(BaseController):
    def __init__(
        self,
        view_model: NavigationViewModel,
        router: Router,
    ) -> None:
        super().__init__(view_model)
        self._router = router
        self._menu_callbacks: dict[str, Callable[[], None]] = {}

    @property
    def vm(self) -> NavigationViewModel:
        return self._view_model

    @property
    def router(self) -> Router:
        return self._router

    def _on_initialize(self) -> None:
        self._connect_signals()
        self._build_sidebar_items()
        self.vm.initialize()

    def _connect_signals(self) -> None:
        self._router.nav_service.navigation_completed.connect(self._on_nav_completed)
        self._router.nav_service.navigation_history_changed.connect(self._on_history_changed)

    def _on_nav_completed(self, route_id: str) -> None:
        self.vm.update_nav_state(
            current=route_id,
            previous=self._router.nav_service.previous_route,
            history=self._router.nav_service.history,
        )
        self.vm.select_item(route_id)

    def _on_history_changed(self, history: list[str]) -> None:
        pass

    def _build_sidebar_items(self) -> None:
        items = []
        for route in self._router.registry.routes:
            items.append({
                "id": route.id,
                "title": route.title,
                "icon": route.icon_name,
                "category": route.category,
                "order": route.order,
            })
        self.vm.set_sidebar_items(items)

    def navigate(self, route_id: str) -> bool:
        return self._router.navigate(route_id)

    def navigate_back(self) -> bool:
        return self._router.navigate_back()

    def navigate_home(self) -> bool:
        return self._router.navigate_home()

    def reload_current(self) -> None:
        self._router.reload_current()

    def register_menu_callback(self, action_id: str, callback: Callable[[], None]) -> None:
        self._menu_callbacks[action_id] = callback

    def on_menu_action(self, action_id: str) -> None:
        callback = self._menu_callbacks.get(action_id)
        if callback:
            callback()
        else:
            self.navigate(action_id)
