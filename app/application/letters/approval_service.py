from __future__ import annotations

from collections.abc import Callable
from typing import Any

from loguru import logger

from app.application.letters.approval_result import ApprovalResult
from app.domain.letters.events import DomainEvent
from app.domain.letters.exceptions import LetterDomainError
from app.domain.letters.interfaces import AuditRepository, LetterRepository, UnitOfWork
from app.domain.letters.letter import Letter
from app.domain.letters.letter_status import LetterStatus
from app.domain.letters.state_machine import is_reviewable


class ApprovalOwnershipError(LetterDomainError):
    def __init__(self, letter_id: str, reviewer_id: str, reason: str) -> None:
        self.letter_id = letter_id
        self.reviewer_id = reviewer_id
        super().__init__(
            f"Reviewer {reviewer_id} not authorized for letter {letter_id}: {reason}",
            code="APPROVAL_OWNERSHIP_ERROR",
        )


class DuplicateApprovalError(LetterDomainError):
    def __init__(self, letter_id: str, action: str) -> None:
        self.letter_id = letter_id
        super().__init__(
            f"Duplicate approval action '{action}' for letter {letter_id}",
            code="DUPLICATE_APPROVAL_ERROR",
        )


class ApprovalService:
    def __init__(
        self,
        letter_repo: LetterRepository,
        audit_repo: AuditRepository,
        uow_factory: Callable[[], UnitOfWork],
    ) -> None:
        self._letter_repo = letter_repo
        self._audit_repo = audit_repo
        self._uow_factory = uow_factory

    def start_review(self, letter_id: str, user_id: str) -> ApprovalResult:
        letter = self._get_letter(letter_id)
        if letter.status == LetterStatus.IN_REVIEW:
            return ApprovalResult.idempotent(letter_id, "START_REVIEW", LetterStatus.IN_REVIEW)
        if letter.status != LetterStatus.PENDING_REVIEW:
            return ApprovalResult.fail(
                letter_id, "START_REVIEW",
                f"Letter must be PENDING_REVIEW, got {letter.status.value}",
                error_code="INVALID_STATUS",
            )
        try:
            letter.start_review(user_id)
        except LetterDomainError as e:
            return ApprovalResult.fail(letter_id, "START_REVIEW", str(e), error_code=e.code)
        return self._commit(letter, "START_REVIEW", user_id)

    def approve(
        self, letter_id: str, user_id: str, reviewer_id: str, notes: str = "",
    ) -> ApprovalResult:
        letter = self._get_letter(letter_id)
        if letter.status == LetterStatus.APPROVED:
            return ApprovalResult.idempotent(letter_id, "APPROVE", LetterStatus.APPROVED)
        self._verify_review_ownership(letter, reviewer_id, "approve")
        try:
            letter.approve(user_id, reviewer_id, notes)
        except LetterDomainError as e:
            return ApprovalResult.fail(letter_id, "APPROVE", str(e), error_code=e.code)
        return self._commit(letter, "APPROVE", reviewer_id)

    def reject(
        self, letter_id: str, user_id: str, reviewer_id: str, reason: str,
    ) -> ApprovalResult:
        letter = self._get_letter(letter_id)
        if letter.status == LetterStatus.REJECTED:
            return ApprovalResult.idempotent(letter_id, "REJECT", LetterStatus.REJECTED)
        self._verify_review_ownership(letter, reviewer_id, "reject")
        try:
            letter.reject(user_id, reviewer_id, reason)
        except LetterDomainError as e:
            return ApprovalResult.fail(letter_id, "REJECT", str(e), error_code=e.code)
        return self._commit(letter, "REJECT", reviewer_id)

    def return_to_draft(self, letter_id: str, user_id: str) -> ApprovalResult:
        letter = self._get_letter(letter_id)
        if letter.status == LetterStatus.DRAFT:
            return ApprovalResult.idempotent(letter_id, "RETURN_TO_DRAFT", LetterStatus.DRAFT)
        try:
            letter.return_to_draft(user_id)
        except LetterDomainError as e:
            return ApprovalResult.fail(letter_id, "RETURN_TO_DRAFT", str(e), error_code=e.code)
        return self._commit(letter, "RETURN_TO_DRAFT", user_id)

    def assign_reviewer(
        self,
        letter_id: str,
        reviewer_id: str,
        reviewer_name: str,
        reviewer_title: str,
        assigned_by: str,
    ) -> ApprovalResult:
        letter = self._get_letter(letter_id)
        if any(r.reviewer_id == reviewer_id and r.is_current for r in letter.reviews):
            return ApprovalResult.idempotent(letter_id, "ASSIGN_REVIEWER", letter.status)
        if not is_reviewable(letter.status):
            return ApprovalResult.fail(
                letter_id, "ASSIGN_REVIEWER",
                f"Letter is not reviewable in status {letter.status.value}",
                error_code="NOT_REVIEWABLE",
            )
        letter.add_review(reviewer_id, reviewer_name, reviewer_title, assigned_by)
        return self._commit(letter, "ASSIGN_REVIEWER", reviewer_id)

    def get_pending_reviews(self, user_id: str, offset: int = 0, limit: int = 50) -> list[Letter]:
        return self._letter_repo.list_by_status(LetterStatus.PENDING_REVIEW, offset, limit)

    def get_in_review(self, user_id: str, offset: int = 0, limit: int = 50) -> list[Letter]:
        return self._letter_repo.list_by_status(LetterStatus.IN_REVIEW, offset, limit)

    def _verify_review_ownership(self, letter: Letter, reviewer_id: str, action: str) -> None:
        if not any(
            r.reviewer_id == reviewer_id and r.is_current
            for r in letter.reviews
        ):
            raise ApprovalOwnershipError(letter.id, reviewer_id, f"Cannot {action}")

    def _get_letter(self, letter_id: str) -> Letter:
        from app.application.letters.letter_service import LetterNotFoundError
        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise LetterNotFoundError(letter_id)
        return letter

    def _commit(self, letter: Letter, action: str, reviewer_id: str | None) -> ApprovalResult:
        events = letter.pop_events()
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                for event in events:
                    self._audit_repo.append(event)
                uow.commit()
            except Exception:
                uow.rollback()
                logger.exception("Rollback on {} for letter {}", action, letter.id)
                return ApprovalResult.fail(
                    letter.id, action,
                    f"{action} failed and rolled back",
                    error_code="ROLLBACK_OCCURRED",
                    status=letter.status,
                )
        event_dicts = [
            {"event_id": e.event_id, "event_type": e.event_type.name, "timestamp": e.timestamp.isoformat()}
            for e in events
        ]
        logger.info("{} for letter {} success", action, letter.id)
        return ApprovalResult.ok(letter.id, action, letter.status, reviewer_id, event_dicts)


__all__ = [
    "ApprovalOwnershipError",
    "ApprovalService",
    "DuplicateApprovalError",
]
