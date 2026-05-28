from __future__ import annotations

from typing import Any

from app.domain.letters.events import DomainEvent, EventType
from app.domain.letters.interfaces import AuditRepository


class AuditService:
    def __init__(self, audit_repo: AuditRepository) -> None:
        self._audit_repo = audit_repo

    def get_letter_history(self, letter_id: str) -> list[DomainEvent]:
        return self._audit_repo.get_events_for_letter(letter_id)

    def get_user_activity(self, user_id: str, limit: int = 50) -> list[DomainEvent]:
        return self._audit_repo.get_events_by_user(user_id, limit)

    def get_creation_event(self, letter_id: str) -> DomainEvent | None:
        events = self._audit_repo.get_events_for_letter(letter_id)
        for event in events:
            if event.event_type == EventType.LETTER_CREATED:
                return event
        return None

    def get_audit_trail(self, letter_id: str) -> list[dict[str, Any]]:
        events = self._audit_repo.get_events_for_letter(letter_id)
        trail = []
        for event in events:
            trail.append({
                "event_id": event.event_id,
                "action": event.event_type.name,
                "user_id": event.user_id,
                "timestamp": event.timestamp.isoformat(),
                "details": event.data,
            })
        return sorted(trail, key=lambda x: x["timestamp"])
