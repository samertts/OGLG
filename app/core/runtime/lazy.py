from __future__ import annotations

import threading
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class LazyLoader(Generic[T]):
    """Thread-safe lazy-loading helper with factory pattern."""

    def __init__(
        self,
        factory: Callable[[], T],
        name: str | None = None,
    ) -> None:
        self._factory = factory
        self._name = name or getattr(factory, "__name__", "unknown")
        self._value: T | None = None
        self._loaded = False
        self._lock = threading.RLock()

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def name(self) -> str:
        return self._name

    def get(self) -> T:
        if not self._loaded:
            with self._lock:
                if not self._loaded:
                    self._value = self._factory()
                    self._loaded = True
        return self._value  # type: ignore[return-value]

    def reset(self) -> None:
        with self._lock:
            self._value = None
            self._loaded = False

    def __repr__(self) -> str:
        status = "loaded" if self._loaded else "pending"
        return f"LazyLoader({self._name}, {status})"
