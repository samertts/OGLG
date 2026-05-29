from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.letters.letter_status import LetterStatus


@dataclass(frozen=True)
class ApprovalResult:
    success: bool
    letter_id: str
    action: str
    status: LetterStatus
    timestamp: datetime
    reviewer_id: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    error_code: str | None = None
    _idempotent: bool = field(default=False, repr=False, compare=False)

    @staticmethod
    def ok(
        letter_id: str,
        action: str,
        status: LetterStatus,
        reviewer_id: str | None = None,
        events: list[dict[str, Any]] | None = None,
    ) -> ApprovalResult:
        return ApprovalResult(
            success=True,
            letter_id=letter_id,
            action=action,
            status=status,
            timestamp=datetime.now(),
            reviewer_id=reviewer_id,
            events=events or [],
        )

    @staticmethod
    def fail(
        letter_id: str,
        action: str,
        error: str,
        error_code: str | None = None,
        status: LetterStatus | None = None,
    ) -> ApprovalResult:
        return ApprovalResult(
            success=False,
            letter_id=letter_id,
            action=action,
            status=status or LetterStatus.DRAFT,
            timestamp=datetime.now(),
            error=error,
            error_code=error_code,
        )

    @staticmethod
    def idempotent(letter_id: str, action: str, status: LetterStatus) -> ApprovalResult:
        now = datetime.now()
        return ApprovalResult(
            success=True,
            letter_id=letter_id,
            action=action,
            status=status,
            timestamp=now,
            _idempotent=True,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "letter_id": self.letter_id,
            "action": self.action,
            "status": self.status.value if self.status else None,
            "timestamp": self.timestamp.isoformat(),
            "reviewer_id": self.reviewer_id,
            "event_count": len(self.events),
            "error": self.error,
            "error_code": self.error_code,
        }

    @property
    def is_ok(self) -> bool:
        return self.success

    @property
    def is_error(self) -> bool:
        return not self.success and self.error is not None

    @property
    def is_idempotent(self) -> bool:
        return self._idempotent or (self.success and self.action == "IDEMPOTENT" and not self.events)


__all__ = [
    "ApprovalResult",
]
