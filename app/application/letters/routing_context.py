from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RoutingContext:
    letter_id: str
    from_department: str
    from_user: str
    to_department: str
    to_user: str
    user_id: str
    notes: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.letter_id:
            errors.append("letter_id is required")
        if not self.from_department:
            errors.append("from_department is required")
        if not self.from_user:
            errors.append("from_user is required")
        if not self.to_department:
            errors.append("to_department is required")
        if not self.to_user:
            errors.append("to_user is required")
        if not self.user_id:
            errors.append("user_id is required")
        return errors

    @property
    def is_self_route(self) -> bool:
        return (
            self.from_department == self.to_department
            and self.from_user == self.to_user
        )

    @property
    def is_same_department(self) -> bool:
        return self.from_department == self.to_department


__all__ = [
    "RoutingContext",
]
