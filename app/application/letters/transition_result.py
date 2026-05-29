from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.letters.letter_status import LetterStatus


@dataclass(frozen=True)
class TransitionResult:
    success: bool
    letter_id: str
    from_status: LetterStatus
    to_status: LetterStatus
    timestamp: datetime
    events: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    error_code: str | None = None
    version: int = 0

    @staticmethod
    def ok(
        letter_id: str,
        from_status: LetterStatus,
        to_status: LetterStatus,
        timestamp: datetime,
        events: list[dict[str, Any]] | None = None,
        version: int = 0,
    ) -> TransitionResult:
        return TransitionResult(
            success=True,
            letter_id=letter_id,
            from_status=from_status,
            to_status=to_status,
            timestamp=timestamp,
            events=events or [],
            version=version,
        )

    @staticmethod
    def fail(
        letter_id: str,
        from_status: LetterStatus,
        to_status: LetterStatus,
        error: str,
        error_code: str | None = None,
        timestamp: datetime | None = None,
    ) -> TransitionResult:
        return TransitionResult(
            success=False,
            letter_id=letter_id,
            from_status=from_status,
            to_status=to_status,
            timestamp=timestamp or datetime.now(),
            error=error,
            error_code=error_code,
        )

    @staticmethod
    def idempotent(
        letter_id: str,
        status: LetterStatus,
        version: int = 0,
    ) -> TransitionResult:
        now = datetime.now()
        return TransitionResult(
            success=True,
            letter_id=letter_id,
            from_status=status,
            to_status=status,
            timestamp=now,
            version=version,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "letter_id": self.letter_id,
            "from_status": self.from_status.value if self.from_status else None,
            "to_status": self.to_status.value if self.to_status else None,
            "timestamp": self.timestamp.isoformat(),
            "event_count": len(self.events),
            "error": self.error,
            "error_code": self.error_code,
            "version": self.version,
        }

    @property
    def is_error(self) -> bool:
        return not self.success and self.error is not None

    @property
    def is_ok(self) -> bool:
        return self.success

    @property
    def is_idempotent(self) -> bool:
        return self.success and self.from_status == self.to_status and not self.events


__all__ = [
    "TransitionResult",
]
