from __future__ import annotations

from enum import Enum


class LetterPriority(Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"

    @property
    def rank(self) -> int:
        return {"LOW": 0, "NORMAL": 1, "HIGH": 2, "URGENT": 3, "CRITICAL": 4}[self.value]

    def __ge__(self, other: LetterPriority) -> bool:
        return self.rank >= other.rank

    def __le__(self, other: LetterPriority) -> bool:
        return self.rank <= other.rank
