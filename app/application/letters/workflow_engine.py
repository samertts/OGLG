from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from loguru import logger

from app.application.letters.transition_context import TransitionContext
from app.application.letters.transition_result import TransitionResult
from app.domain.letters.exceptions import LetterDomainError, StateTransitionError
from app.domain.letters.interfaces import AuditRepository, LetterRepository, UnitOfWork
from app.domain.letters.letter import Letter
from app.domain.letters.letter_status import LetterStatus

_HandlerFn = Callable[[Letter, str, dict[str, Any]], None]

WORKFLOW_STATUSES: frozenset[LetterStatus] = frozenset({
    LetterStatus.DRAFT,
    LetterStatus.IN_REVIEW,
    LetterStatus.APPROVED,
    LetterStatus.REJECTED,
    LetterStatus.DELIVERED,
    LetterStatus.ARCHIVED,
    LetterStatus.RESTORED,
    LetterStatus.DELETED,
})

_ALLOWED_WORKFLOW_MATRIX: dict[LetterStatus, set[LetterStatus]] = {
    LetterStatus.DRAFT: {LetterStatus.IN_REVIEW, LetterStatus.DELETED},
    LetterStatus.IN_REVIEW: {LetterStatus.APPROVED, LetterStatus.REJECTED, LetterStatus.DRAFT},
    LetterStatus.APPROVED: {LetterStatus.DELIVERED, LetterStatus.ARCHIVED},
    LetterStatus.REJECTED: {LetterStatus.DRAFT, LetterStatus.DELETED},
    LetterStatus.DELIVERED: {LetterStatus.ARCHIVED, LetterStatus.RESTORED},
    LetterStatus.ARCHIVED: {LetterStatus.RESTORED, LetterStatus.DELETED},
    LetterStatus.RESTORED: {LetterStatus.DRAFT, LetterStatus.ARCHIVED},
    LetterStatus.DELETED: set(),
}


def _submit_and_start_review(letter: Letter, user_id: str, metadata: dict[str, Any]) -> None:
    letter.submit_for_review(user_id)
    letter.start_review(user_id)


def _approve(letter: Letter, user_id: str, metadata: dict[str, Any]) -> None:
    reviewer_id = metadata.get("reviewer_id", user_id)
    notes = metadata.get("notes", "")
    letter.approve(user_id, reviewer_id, notes)


def _reject(letter: Letter, user_id: str, metadata: dict[str, Any]) -> None:
    reviewer_id = metadata.get("reviewer_id", user_id)
    reason = metadata.get("reason", "Rejected")
    letter.reject(user_id, reviewer_id, reason)


def _return_to_draft(letter: Letter, user_id: str, metadata: dict[str, Any]) -> None:
    letter.return_to_draft(user_id)


def _sent_and_delivered(letter: Letter, user_id: str, metadata: dict[str, Any]) -> None:
    letter.mark_sent(user_id)
    proof = metadata.get("proof")
    letter.mark_delivered(user_id, proof)


def _archive(letter: Letter, user_id: str, metadata: dict[str, Any]) -> None:
    reason = metadata.get("reason", "")
    letter.archive(user_id, reason)


def _restore(letter: Letter, user_id: str, metadata: dict[str, Any]) -> None:
    reason = metadata.get("reason", "")
    letter.restore(user_id, reason)


def _soft_delete(letter: Letter, user_id: str, metadata: dict[str, Any]) -> None:
    reason = metadata.get("reason", "")
    letter.soft_delete(user_id, reason)


_TRANSITION_HANDLERS: dict[tuple[LetterStatus, LetterStatus], _HandlerFn] = {
    (LetterStatus.DRAFT, LetterStatus.IN_REVIEW): _submit_and_start_review,
    (LetterStatus.DRAFT, LetterStatus.DELETED): _soft_delete,
    (LetterStatus.IN_REVIEW, LetterStatus.APPROVED): _approve,
    (LetterStatus.IN_REVIEW, LetterStatus.REJECTED): _reject,
    (LetterStatus.IN_REVIEW, LetterStatus.DRAFT): _return_to_draft,
    (LetterStatus.APPROVED, LetterStatus.DELIVERED): _sent_and_delivered,
    (LetterStatus.APPROVED, LetterStatus.ARCHIVED): _archive,
    (LetterStatus.REJECTED, LetterStatus.DRAFT): _return_to_draft,
    (LetterStatus.REJECTED, LetterStatus.DELETED): _soft_delete,
    (LetterStatus.DELIVERED, LetterStatus.ARCHIVED): _archive,
    (LetterStatus.DELIVERED, LetterStatus.RESTORED): _restore,
    (LetterStatus.ARCHIVED, LetterStatus.RESTORED): _restore,
    (LetterStatus.ARCHIVED, LetterStatus.DELETED): _soft_delete,
    (LetterStatus.RESTORED, LetterStatus.DRAFT): _return_to_draft,
    (LetterStatus.RESTORED, LetterStatus.ARCHIVED): _archive,
}


class WorkflowEngineExecutionError(LetterDomainError):
    def __init__(self, letter_id: str, message: str) -> None:
        self.letter_id = letter_id
        super().__init__(message, code="WORKFLOW_EXECUTION_ERROR")


class WorkflowEngine:
    def __init__(
        self,
        letter_repo: LetterRepository,
        audit_repo: AuditRepository,
        uow_factory: Callable[[], UnitOfWork],
    ) -> None:
        self._letter_repo = letter_repo
        self._audit_repo = audit_repo
        self._uow_factory = uow_factory

    def execute(self, ctx: TransitionContext) -> TransitionResult:
        ctx.validate()
        letter = self._letter_repo.get_by_id(ctx.letter_id)
        if letter is None:
            return TransitionResult.fail(
                ctx.letter_id, ctx.from_status, ctx.target_status,
                error=f"Letter not found: {ctx.letter_id}",
                error_code="LETTER_NOT_FOUND",
            )
        if ctx.from_status != letter.status:
            return TransitionResult.fail(
                ctx.letter_id, ctx.from_status, ctx.target_status,
                error=f"Status mismatch: expected {ctx.from_status.value}, actual {letter.status.value}",
                error_code="STATUS_MISMATCH",
            )
        actual_from = letter.status
        if actual_from not in WORKFLOW_STATUSES:
            return TransitionResult.fail(
                ctx.letter_id, actual_from, ctx.target_status,
                error=f"Unsupported source status: {actual_from.value}",
                error_code="UNSUPPORTED_SOURCE_STATUS",
            )
        if ctx.target_status not in WORKFLOW_STATUSES:
            return TransitionResult.fail(
                ctx.letter_id, actual_from, ctx.target_status,
                error=f"Unsupported target status: {ctx.target_status.value}",
                error_code="UNSUPPORTED_TARGET_STATUS",
            )
        if actual_from == ctx.target_status:
            return TransitionResult.idempotent(ctx.letter_id, actual_from, letter.version)

        allowed = _ALLOWED_WORKFLOW_MATRIX.get(actual_from, set())
        if ctx.target_status not in allowed:
            return TransitionResult.fail(
                ctx.letter_id, actual_from, ctx.target_status,
                error=f"Cannot transition from {actual_from.value} to {ctx.target_status.value}",
                error_code="TRANSITION_NOT_ALLOWED",
            )

        handler = _TRANSITION_HANDLERS.get((actual_from, ctx.target_status))
        if handler is None:
            return TransitionResult.fail(
                ctx.letter_id, actual_from, ctx.target_status,
                error=f"No handler for transition {actual_from.value} -> {ctx.target_status.value}",
                error_code="NO_HANDLER",
            )

        execution_ts = ctx.timestamp if ctx.timestamp else datetime.now()
        try:
            handler(letter, ctx.user_id, ctx.metadata)
        except StateTransitionError as e:
            return TransitionResult.fail(
                ctx.letter_id, actual_from, ctx.target_status,
                error=str(e), error_code="STATE_TRANSITION_ERROR",
                timestamp=execution_ts,
            )
        except LetterDomainError as e:
            return TransitionResult.fail(
                ctx.letter_id, actual_from, ctx.target_status,
                error=str(e), error_code=e.code or "DOMAIN_ERROR",
                timestamp=execution_ts,
            )

        events = letter.pop_events()
        version = letter.version

        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                for event in events:
                    self._audit_repo.append(event)
                uow.commit()
            except Exception:
                uow.rollback()
                logger.exception("Transition rollback for letter {}", ctx.letter_id)
                return TransitionResult.fail(
                    ctx.letter_id, actual_from, ctx.target_status,
                    error="Transition failed and rolled back",
                    error_code="ROLLBACK_OCCURRED",
                    timestamp=execution_ts,
                )

        event_dicts = [
            {
                "event_id": e.event_id,
                "event_type": e.event_type.name,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "user_id": e.user_id,
            }
            for e in events
        ]

        logger.info(
            "Transition {} -> {} for letter {} ({} events)",
            actual_from.value, ctx.target_status.value, ctx.letter_id, len(events),
        )
        return TransitionResult.ok(
            ctx.letter_id, actual_from, ctx.target_status,
            timestamp=execution_ts, events=event_dicts, version=version,
        )

    def can_transition(self, from_status: LetterStatus, to_status: LetterStatus) -> bool:
        if from_status not in WORKFLOW_STATUSES or to_status not in WORKFLOW_STATUSES:
            return False
        allowed = _ALLOWED_WORKFLOW_MATRIX.get(from_status, set())
        return to_status in allowed

    def get_allowed_targets(self, status: LetterStatus) -> list[LetterStatus]:
        if status not in WORKFLOW_STATUSES:
            return []
        return list(_ALLOWED_WORKFLOW_MATRIX.get(status, set()))


__all__ = [
    "WorkflowEngine",
    "WorkflowEngineExecutionError",
    "WORKFLOW_STATUSES",
]
