from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReviewAssignment:
    id: str
    reviewer_id: str
    reviewer_name: str
    reviewer_title: str
    assigned_at: datetime
    completed_at: datetime | None = None
    action: str | None = None
    notes: str = ""
    is_current: bool = True
    assigned_by: str = ""

    @staticmethod
    def create(
        reviewer_id: str,
        reviewer_name: str,
        reviewer_title: str,
        assigned_by: str,
    ) -> ReviewAssignment:
        return ReviewAssignment(
            id=str(uuid.uuid4()),
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            reviewer_title=reviewer_title,
            assigned_at=datetime.now(),
            is_current=True,
            assigned_by=assigned_by,
        )

    def complete(self, action: str, notes: str = "") -> None:
        self.completed_at = datetime.now()
        self.action = action
        self.notes = notes
        self.is_current = False
