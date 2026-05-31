from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class StateBoundary:
    max_items: int = 10_000
    max_string_length: int = 10_000
    max_nesting_depth: int = 5
    allowed_types: tuple[type, ...] = (str, int, float, bool, type(None), list, dict)
    forbid_none: bool = False

    def validate(self, value: Any, depth: int = 0) -> bool:
        if value is None:
            return not self.forbid_none
        if depth > self.max_nesting_depth:
            return False
        if isinstance(value, (str, bytes)):
            if len(value) > self.max_string_length:
                return False
            if isinstance(value, bytes):
                return False
        if isinstance(value, (list, tuple)):
            if len(value) > self.max_items:
                return False
            for item in value:
                if not self.validate(item, depth + 1):
                    return False
        if isinstance(value, dict):
            if len(value) > self.max_items:
                return False
            for k, v in value.items():
                if isinstance(k, str) and len(k) > self.max_string_length:
                    return False
                if not self.validate(v, depth + 1):
                    return False
        if not isinstance(value, self.allowed_types):
            return False
        return True


class BoundedState(Generic[T]):
    def __init__(self, initial: T, boundary: StateBoundary | None = None):
        self._value = initial
        self._boundary = boundary or StateBoundary()
        if not self._boundary.validate(initial):
            raise ValueError("Initial value violates state boundary")

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        if not self._boundary.validate(new_value):
            raise ValueError("Value violates state boundary")
        self._value = new_value

    @property
    def boundary(self) -> StateBoundary:
        return self._boundary
