from __future__ import annotations

from app.ui.viewmodels.base_viewmodel import BaseViewModel, ViewModelProperty, ViewModelState


class NavigationViewModel(BaseViewModel):
    def __init__(self) -> None:
        super().__init__()
        self.current_route: ViewModelProperty[str | None] = ViewModelProperty(None)
        self.previous_route: ViewModelProperty[str | None] = ViewModelProperty(None)
        self.can_go_back: ViewModelProperty[bool] = ViewModelProperty(False)
        self.can_go_forward: ViewModelProperty[bool] = ViewModelProperty(False)
        self.is_navigating: ViewModelProperty[bool] = ViewModelProperty(False)
        self.route_history: ViewModelProperty[list[str]] = ViewModelProperty([])
        self.nav_path: ViewModelProperty[list[str]] = ViewModelProperty([])
        self.sidebar_items: ViewModelProperty[list[dict]] = ViewModelProperty([])
        self.selected_item: ViewModelProperty[str | None] = ViewModelProperty(None)

    def initialize(self) -> None:
        self.state = ViewModelState.LOADING
        self.state = ViewModelState.READY

    def update_nav_state(
        self,
        current: str | None,
        previous: str | None,
        history: list[str],
    ) -> None:
        self.current_route.set(current)
        self.previous_route.set(previous)
        self.can_go_back.set(len(history) > 0)
        self.route_history.set(history)
        path = list(history)
        if current:
            path.append(current)
        self.nav_path.set(path)

    def set_sidebar_items(self, items: list[dict]) -> None:
        self.sidebar_items.set(items)

    def select_item(self, item_id: str | None) -> None:
        self.selected_item.set(item_id)
