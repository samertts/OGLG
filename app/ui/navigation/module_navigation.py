from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from loguru import logger

from app.ui.navigation.screen_router import ScreenEntry, ScreenRegistry, ScreenRouter
from app.ui.viewmodels.base_viewmodel import ScreenViewModel


@dataclass
class ModuleDefinition:
    id: str
    title: str
    icon_name: str = ""
    category: str = "main"
    order: int = 0
    requires_auth: bool = False
    requires_setup: bool = False
    required_permissions: list[str] = field(default_factory=list)
    lazy_load: bool = True


class ModuleRegistry:
    def __init__(self) -> None:
        self._modules: dict[str, ModuleDefinition] = {}

    def register(self, module: ModuleDefinition) -> None:
        if module.id in self._modules:
            raise ValueError(f"Module already registered: {module.id}")
        self._modules[module.id] = module
        logger.debug(f"Module registered: {module.id}")

    def get(self, module_id: str) -> ModuleDefinition | None:
        return self._modules.get(module_id)

    @property
    def modules(self) -> list[ModuleDefinition]:
        return sorted(self._modules.values(), key=lambda m: m.order)

    @property
    def module_ids(self) -> list[str]:
        return [m.id for m in self.modules]

    def categories(self) -> dict[str, list[ModuleDefinition]]:
        cats: dict[str, list[ModuleDefinition]] = {}
        for m in self.modules:
            cats.setdefault(m.category, []).append(m)
        return cats


class ScreenFactory:
    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], tuple[ScreenViewModel, object, object]]] = {}

    def register_factory(
        self,
        screen_id: str,
        factory: Callable[[], tuple[ScreenViewModel, object, object]],
    ) -> None:
        self._factories[screen_id] = factory

    def create(self, screen_id: str) -> tuple[ScreenViewModel, object, object] | None:
        factory = self._factories.get(screen_id)
        if factory is None:
            return None
        return factory()


class ModuleNavigationBuilder:
    def __init__(
        self,
        module_registry: ModuleRegistry,
        screen_factory: ScreenFactory,
        screen_registry: ScreenRegistry,
    ) -> None:
        self._module_registry = module_registry
        self._screen_factory = screen_factory
        self._screen_registry = screen_registry

    def build_screens(self) -> ScreenRouter:
        for module in self._module_registry.modules:
            result = self._screen_factory.create(module.id)
            if result is None:
                logger.warning(f"No factory for module: {module.id}")
                continue
            view_model, controller, widget = result
            entry = ScreenEntry(
                id=module.id,
                view_model=view_model,
                controller=controller,
                widget=widget,
                title=module.title,
                icon_name=module.icon_name,
                category=module.category,
                order=module.order,
                lazy_loaded=module.lazy_load,
            )
            self._screen_registry.register(entry)
        return ScreenRouter(self._screen_registry)
