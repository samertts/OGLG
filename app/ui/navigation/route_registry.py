from __future__ import annotations

from dataclasses import dataclass

from loguru import logger


@dataclass(frozen=True)
class RouteDefinition:
    id: str
    title: str
    icon_name: str = ""
    category: str = "main"
    order: int = 0
    requires_auth: bool = False
    lazy_load: bool = True
    parent_id: str | None = None
    keywords: tuple[str, ...] = ()


class RouteRegistry:
    def __init__(self) -> None:
        self._routes: dict[str, RouteDefinition] = {}
        self._aliases: dict[str, str] = {}

    def register(self, route: RouteDefinition) -> None:
        if route.id in self._routes:
            raise ValueError(f"Route already registered: {route.id}")
        self._routes[route.id] = route
        logger.debug(f"Route registered: {route.id}")

    def register_alias(self, alias: str, target_id: str) -> None:
        if target_id not in self._routes:
            raise ValueError(f"Target route not found for alias: {target_id}")
        self._aliases[alias] = target_id
        logger.debug(f"Route alias: {alias} -> {target_id}")

    def get(self, route_id: str) -> RouteDefinition | None:
        resolved = self._aliases.get(route_id, route_id)
        return self._routes.get(resolved)

    def resolve(self, route_id: str) -> str:
        return self._aliases.get(route_id, route_id)

    @property
    def routes(self) -> list[RouteDefinition]:
        return sorted(self._routes.values(), key=lambda r: r.order)

    @property
    def route_ids(self) -> list[str]:
        return [r.id for r in self.routes]

    def get_by_category(self, category: str) -> list[RouteDefinition]:
        return [r for r in self.routes if r.category == category]

    def categories(self) -> dict[str, list[RouteDefinition]]:
        result: dict[str, list[RouteDefinition]] = {}
        for r in self.routes:
            result.setdefault(r.category, []).append(r)
        return result

    def search(self, query: str) -> list[RouteDefinition]:
        q = query.lower()
        return [
            r for r in self.routes
            if q in r.title.lower()
            or q in r.id.lower()
            or any(q in kw.lower() for kw in r.keywords)
        ]

    def parent_children(self) -> dict[str | None, list[RouteDefinition]]:
        result: dict[str | None, list[RouteDefinition]] = {}
        for r in self.routes:
            result.setdefault(r.parent_id, []).append(r)
        return result

    def __contains__(self, route_id: str) -> bool:
        return route_id in self._routes or route_id in self._aliases

    def __len__(self) -> int:
        return len(self._routes)

    def __repr__(self) -> str:
        return f"RouteRegistry({len(self._routes)} routes, {len(self._aliases)} aliases)"
