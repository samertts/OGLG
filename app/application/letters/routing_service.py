from __future__ import annotations

from collections.abc import Callable

from loguru import logger

from app.application.letters.routing_context import RoutingContext
from app.application.letters.routing_result import RoutingResult
from app.domain.letters.events import DomainEvent, EventType
from app.domain.letters.exceptions import LetterDomainError
from app.domain.letters.interfaces import AuditRepository, LetterRepository, UnitOfWork
from app.domain.letters.letter import Letter
from app.domain.letters.routing_step import RoutingStep


class RoutingValidationError(LetterDomainError):
    def __init__(self, letter_id: str, reason: str) -> None:
        self.letter_id = letter_id
        super().__init__(f"Routing validation failed for letter {letter_id}: {reason}", code="ROUTING_VALIDATION_ERROR")


class SelfRouteError(RoutingValidationError):
    def __init__(self, letter_id: str, department: str, user: str) -> None:
        super().__init__(letter_id, f"Self-route detected: {department}/{user}")
        self.department = department
        self.user = user


class CircularRouteError(RoutingValidationError):
    def __init__(self, letter_id: str, department: str) -> None:
        super().__init__(letter_id, f"Circular route detected: already routed to {department}")
        self.department = department


class InvalidDepartmentError(RoutingValidationError):
    def __init__(self, letter_id: str, department: str, reason: str) -> None:
        super().__init__(letter_id, f"Invalid department {department}: {reason}")
        self.department = department


class RoutingService:
    def __init__(
        self,
        letter_repo: LetterRepository,
        audit_repo: AuditRepository,
        uow_factory: Callable[[], UnitOfWork],
    ) -> None:
        self._letter_repo = letter_repo
        self._audit_repo = audit_repo
        self._uow_factory = uow_factory

    def route_forward(self, ctx: RoutingContext) -> RoutingResult:
        validation_errors = ctx.validate()
        if validation_errors:
            return RoutingResult.fail(ctx.letter_id, "ROUTE", "; ".join(validation_errors), error_code="VALIDATION_ERROR")
        letter = self._get_letter(ctx.letter_id)
        route_errors = self._validate_route(letter, ctx)
        if route_errors:
            return route_errors
        step = RoutingStep.create(
            from_department=ctx.from_department,
            from_user=ctx.from_user,
            to_department=ctx.to_department,
            to_user=ctx.to_user,
            action="ROUTE",
            notes=ctx.notes,
        )
        letter.add_routing_step(step)
        self._append_routing_event(letter, ctx.user_id, ctx.from_department, ctx.to_department)
        return self._commit(letter, "ROUTE", ctx.from_department, ctx.to_department)

    def accept_routing(self, letter_id: str, user_id: str, department: str) -> RoutingResult:
        letter = self._get_letter(letter_id)
        if not letter.routing_history:
            return RoutingResult.fail(letter_id, "ACCEPT", "No routing history to accept", error_code="NO_ROUTING_HISTORY")
        step = RoutingStep.create(
            from_department=department,
            from_user=user_id,
            to_department=department,
            to_user=user_id,
            action="ACCEPT",
        )
        letter.add_routing_step(step)
        return self._commit(letter, "ACCEPT", department, department)

    def reject_routing(self, letter_id: str, user_id: str, department: str, reason: str) -> RoutingResult:
        letter = self._get_letter(letter_id)
        if not letter.routing_history:
            return RoutingResult.fail(letter_id, "REJECT", "No routing history to reject", error_code="NO_ROUTING_HISTORY")
        step = RoutingStep.create(
            from_department=department,
            from_user=user_id,
            to_department=department,
            to_user=user_id,
            action="REJECT",
            notes=reason,
        )
        letter.add_routing_step(step)
        return self._commit(letter, "REJECT", department, department)

    def get_routing_history(self, letter_id: str) -> list[RoutingStep]:
        letter = self._get_letter(letter_id)
        return list(letter.routing_history)

    def _validate_route(self, letter: Letter, ctx: RoutingContext) -> RoutingResult | None:
        if ctx.is_self_route:
            return RoutingResult.fail(
                ctx.letter_id, "ROUTE",
                f"Self-route: from {ctx.from_department}/{ctx.from_user} to same destination",
                error_code="SELF_ROUTE",
                from_department=ctx.from_department,
                to_department=ctx.to_department,
            )
        visited_departments: set[str] = set()
        for step in letter.routing_history:
            visited_departments.add(step.from_department)
            visited_departments.add(step.to_department)
        if letter.department_id:
            visited_departments.add(letter.department_id)
        if ctx.to_department in visited_departments:
            return RoutingResult.fail(
                ctx.letter_id, "ROUTE",
                f"Circular route: letter already routed to {ctx.to_department}",
                error_code="CIRCULAR_ROUTE",
                from_department=ctx.from_department,
                to_department=ctx.to_department,
            )
        return None

    def _append_routing_event(
        self, letter: Letter, user_id: str, from_dept: str, to_dept: str,
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

    def _commit(self, letter: Letter, action: str, from_dept: str, to_dept: str) -> RoutingResult:
        events = letter.pop_events()
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                for event in events:
                    self._audit_repo.append(event)
                uow.commit()
            except Exception:
                uow.rollback()
                logger.exception("Rollback on {} routing for letter {}", action, letter.id)
                return RoutingResult.fail(
                    letter.id, action,
                    f"{action} routing failed and rolled back",
                    error_code="ROLLBACK_OCCURRED",
                    from_department=from_dept,
                    to_department=to_dept,
                )
        event_dicts = [
            {"event_id": e.event_id, "event_type": e.event_type.name, "timestamp": e.timestamp.isoformat()}
            for e in events
        ]
        logger.info("Routing {} for letter {} success", action, letter.id)
        return RoutingResult.ok(letter.id, action, from_dept, to_dept, event_dicts)


__all__ = [
    "CircularRouteError",
    "InvalidDepartmentError",
    "RoutingService",
    "RoutingValidationError",
    "SelfRouteError",
]
