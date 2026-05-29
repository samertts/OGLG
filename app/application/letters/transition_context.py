from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.letters.letter_status import LetterStatus


@dataclass(frozen=True)
class TransitionContext:
    letter_id: str
    from_status: LetterStatus
    target_status: LetterStatus
    user_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.letter_id:
            raise ValueError("letter_id is required")
        if self.from_status is None:
            raise ValueError("from_status is required")
        if self.target_status is None:
            raise ValueError("target_status is required")
        if not self.user_id:
            raise ValueError("user_id is required")


__all__ = [
    "TransitionContext",
]
