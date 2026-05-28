from __future__ import annotations

from enum import Enum


class LetterClassification(Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"
    TOP_SECRET = "TOP_SECRET"

    @property
    def requires_clearance(self) -> bool:
        return self in (LetterClassification.SECRET, LetterClassification.TOP_SECRET)

    @property
    def level(self) -> int:
        return {"PUBLIC": 0, "INTERNAL": 1, "CONFIDENTIAL": 2, "SECRET": 3, "TOP_SECRET": 4}[self.value]
