from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RoutingStep:
    id: str
    from_department: str
    from_user: str
    to_department: str
    to_user: str
    routed_at: datetime
    action: str
    notes: str = ""
    completed_at: datetime | None = None

    @staticmethod
    def create(
        from_department: str,
        from_user: str,
        to_department: str,
        to_user: str,
        action: str,
        notes: str = "",
    ) -> RoutingStep:
        return RoutingStep(
            id=str(uuid.uuid4()),
            from_department=from_department,
            from_user=from_user,
            to_department=to_department,
            to_user=to_user,
            routed_at=datetime.now(),
            action=action,
            notes=notes,
        )
