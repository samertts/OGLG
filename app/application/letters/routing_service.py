from __future__ import annotations

from typing import Any

from loguru import logger

from app.domain.letters.events import DomainEvent, EventType
from app.domain.letters.interfaces import AuditRepository, LetterRepository
from app.domain.letters.letter import Letter
from app.domain.letters.routing_step import RoutingStep


class RoutingServiceError(Exception):
    pass


class RoutingService:
    def __init__(
        self,
        letter_repo: LetterRepository,
        audit_repo: AuditRepository,
        uow_factory: Any,
    ) -> None:
        self._letter_repo = letter_repo
        self._audit_repo = audit_repo
        self._uow_factory = uow_factory

    def route_forward(
        self,
        letter_id: str,
        from_user: str,
        from_department: str,
        to_user: str,
        to_department: str,
        user_id: str,
        notes: str = "",
    ) -> Letter:
        letter = self._get_letter(letter_id)
        step = RoutingStep.create(
            from_department=from_department,
            from_user=from_user,
            to_department=to_department,
            to_user=to_user,
            action="ROUTE",
            notes=notes,
        )
        letter.add_routing_step(step)
        self._generate_routing_event(letter, user_id, from_department, to_department)
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter.pop_events())
                uow.commit()
                logger.info("Routed letter {} from {} to {}", letter_id, from_department, to_department)
            except Exception:
                uow.rollback()
                raise
        return letter

    def accept_routing(self, letter_id: str, user_id: str, department: str) -> Letter:
        letter = self._get_letter(letter_id)
        step = RoutingStep.create(
            from_department=department,
            from_user=user_id,
            to_department=department,
            to_user=user_id,
            action="ACCEPT",
        )
        letter.add_routing_step(step)
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter.pop_events())
                uow.commit()
                logger.info("Accepted routing for letter {} at {}", letter_id, department)
            except Exception:
                uow.rollback()
                raise
        return letter

    def reject_routing(
        self, letter_id: str, user_id: str, department: str, reason: str
    ) -> Letter:
        letter = self._get_letter(letter_id)
        step = RoutingStep.create(
            from_department=department,
            from_user=user_id,
            to_department=department,
            to_user=user_id,
            action="REJECT",
            notes=reason,
        )
        letter.add_routing_step(step)
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter.pop_events())
                uow.commit()
                logger.info("Rejected routing for letter {}: {}", letter_id, reason)
            except Exception:
                uow.rollback()
                raise
        return letter

    def get_routing_history(self, letter_id: str) -> list[RoutingStep]:
        letter = self._get_letter(letter_id)
        return list(letter.routing_history)

    def _generate_routing_event(
        self, letter: Letter, user_id: str, from_dept: str, to_dept: str
    ) -> None:
        import uuid
        from datetime import datetime

        event = DomainEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LETTER_ROUTED,
            aggregate_id=letter.id,
            timestamp=datetime.now(),
            user_id=user_id,
            data={"from_department": from_dept, "to_department": to_dept},
        )
        letter._events.append(event)

    def _get_letter(self, letter_id: str) -> Letter:
        from app.application.letters.letter_service import LetterNotFoundError

        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise LetterNotFoundError(letter_id)
        return letter

    def _persist_events(self, events: list[DomainEvent]) -> None:
        for event in events:
            self._audit_repo.append(event)
