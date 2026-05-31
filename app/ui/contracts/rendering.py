from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Generator


@dataclass
class BoundedRender:
    max_widgets: int = 500
    max_depth: int = 20
    max_update_ms: int = 50

    def within_bounds(self, widget_count: int, depth: int) -> bool:
        return widget_count <= self.max_widgets and depth <= self.max_depth


class RenderGuard:
    def __init__(
        self,
        on_crash: Callable[[Exception], None] | None = None,
        bounds: BoundedRender | None = None,
    ):
        self._on_crash = on_crash
        self._bounds = bounds or BoundedRender()
        self._depth = 0

    @contextmanager
    def protect(self) -> Generator[None, Any, None]:
        try:
            self._depth += 1
            if self._depth > self._bounds.max_depth:
                raise RuntimeError("Max render depth exceeded")
            yield
        except Exception as e:
            if self._on_crash:
                self._on_crash(e)
        finally:
            self._depth -= 1

    def reset_depth(self) -> None:
        self._depth = 0
