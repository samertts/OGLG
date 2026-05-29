from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RoutingResult:
    success: bool
    letter_id: str
    action: str
    from_department: str
    to_department: str
    timestamp: datetime
    events: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    error_code: str | None = None
    routing_step_index: int = 0

    @staticmethod
    def ok(
        letter_id: str,
        action: str,
        from_department: str,
        to_department: str,
        events: list[dict[str, Any]] | None = None,
        routing_step_index: int = 0,
    ) -> RoutingResult:
        return RoutingResult(
            success=True,
            letter_id=letter_id,
            action=action,
            from_department=from_department,
            to_department=to_department,
            timestamp=datetime.now(),
            events=events or [],
            routing_step_index=routing_step_index,
        )

    @staticmethod
    def fail(
        letter_id: str,
        action: str,
        error: str,
        error_code: str | None = None,
        from_department: str = "",
        to_department: str = "",
    ) -> RoutingResult:
        return RoutingResult(
            success=False,
            letter_id=letter_id,
            action=action,
            from_department=from_department,
            to_department=to_department,
            timestamp=datetime.now(),
            error=error,
            error_code=error_code,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "letter_id": self.letter_id,
            "action": self.action,
            "from_department": self.from_department,
            "to_department": self.to_department,
            "timestamp": self.timestamp.isoformat(),
            "event_count": len(self.events),
            "routing_step_index": self.routing_step_index,
            "error": self.error,
            "error_code": self.error_code,
        }

    @property
    def is_ok(self) -> bool:
        return self.success

    @property
    def is_error(self) -> bool:
        return not self.success and self.error is not None


__all__ = [
    "RoutingResult",
]
