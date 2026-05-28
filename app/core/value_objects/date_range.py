from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class DateRange:
    """Date range value object for queries and filters."""

    start_date: date | None = None
    end_date: date | None = None

    @classmethod
    def from_datetime(cls, start: datetime | None, end: datetime | None) -> DateRange:
        return cls(
            start_date=start.date() if start else None,
            end_date=end.date() if end else None,
        )

    @classmethod
    def from_strings(cls, start: str | None, end: str | None) -> DateRange:
        return cls(
            start_date=date.fromisoformat(start) if start else None,
            end_date=date.fromisoformat(end) if end else None,
        )

    def contains(self, d: date) -> bool:
        if self.start_date and d < self.start_date:
            return False
        if self.end_date and d > self.end_date:
            return False
        return True

    def is_empty(self) -> bool:
        return self.start_date is None and self.end_date is None
