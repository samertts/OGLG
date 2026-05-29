from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class NumberingContext:
    department_code: str
    year: int | None = None

    def __post_init__(self) -> None:
        if not self.department_code or not self.department_code.strip():
            raise ValueError("department_code cannot be empty")
        if len(self.department_code) > 10:
            raise ValueError(f"department_code too long: {self.department_code}")
        if self.year is not None and (self.year < 1900 or self.year > 2099):
            raise ValueError(f"year out of range: {self.year}")

    @property
    def effective_year(self) -> int:
        return self.year if self.year is not None else datetime.now().year

    def to_dict(self) -> dict[str, Any]:
        return {
            "department_code": self.department_code,
            "year": self.year,
        }


__all__ = [
    "NumberingContext",
]
