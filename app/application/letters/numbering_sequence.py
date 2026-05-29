from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class NumberingSequence:
    prefix: str
    year: int
    last_sequence: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime | None = None

    def next_value(self) -> int:
        return self.last_sequence + 1

    def with_increment(self, count: int = 1) -> NumberingSequence:
        return NumberingSequence(
            prefix=self.prefix,
            year=self.year,
            last_sequence=self.last_sequence + count,
            created_at=self.created_at,
            updated_at=datetime.now(),
        )

    def to_dict(self) -> dict:
        return {
            "prefix": self.prefix,
            "year": self.year,
            "last_sequence": self.last_sequence,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def effective_year(self) -> int:
        return self.year


__all__ = [
    "NumberingSequence",
]
