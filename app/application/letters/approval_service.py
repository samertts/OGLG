from __future__ import annotations

from typing import Any

from loguru import logger

from app.domain.letters.events import DomainEvent
from app.domain.letters.interfaces import AuditRepository, LetterRepository
from app.domain.letters.letter import Letter
from app.domain.letters.letter_status import LetterStatus


class ApprovalServiceError(Exception):
    pass


class ApprovalService:
    def __init__(
        self,
        letter_repo: LetterRepository,
        audit_repo: AuditRepository,
        uow_factory: Any,
    ) -> None:
        self._letter_repo = letter_repo
        self._audit_repo = audit_repo
        self._uow_factory = uow_factory

    def start_review(self, letter_id: str, user_id: str) -> Letter:
        letter = self._get_letter(letter_id)
        try:
            letter.start_review(user_id)
        except Exception as e:
            raise ApprovalServiceError(f"Cannot start review for {letter_id}: {e}") from e
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter.pop_events())
                uow.commit()
                logger.info("Started review for letter {}", letter_id)
            except Exception:
                uow.rollback()
                raise
        return letter

    def approve(self, letter_id: str, user_id: str, reviewer_id: str, notes: str = "") -> Letter:
        letter = self._get_letter(letter_id)
        try:
            letter.approve(user_id, reviewer_id, notes)
        except Exception as e:
            raise ApprovalServiceError(f"Cannot approve letter {letter_id}: {e}") from e
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter.pop_events())
                uow.commit()
                logger.info("Approved letter {} by {}", letter_id, reviewer_id)
            except Exception:
                uow.rollback()
                raise
        return letter

    def reject(self, letter_id: str, user_id: str, reviewer_id: str, reason: str) -> Letter:
        letter = self._get_letter(letter_id)
        try:
            letter.reject(user_id, reviewer_id, reason)
        except Exception as e:
            raise ApprovalServiceError(f"Cannot reject letter {letter_id}: {e}") from e
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter.pop_events())
                uow.commit()
                logger.info("Rejected letter {}: {}", letter_id, reason)
            except Exception:
                uow.rollback()
                raise
        return letter

    def return_to_draft(self, letter_id: str, user_id: str) -> Letter:
        letter = self._get_letter(letter_id)
        try:
            letter.return_to_draft(user_id)
        except Exception as e:
            raise ApprovalServiceError(f"Cannot return letter {letter_id} to draft: {e}") from e
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter.pop_events())
                uow.commit()
                logger.info("Returned letter {} to draft", letter_id)
            except Exception:
                uow.rollback()
                raise
        return letter

    def assign_reviewer(
        self,
        letter_id: str,
        reviewer_id: str,
        reviewer_name: str,
        reviewer_title: str,
        assigned_by: str,
    ) -> Letter:
        letter = self._get_letter(letter_id)
        letter.add_review(reviewer_id, reviewer_name, reviewer_title, assigned_by)
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter.pop_events())
                uow.commit()
                logger.info("Assigned reviewer {} to letter {}", reviewer_id, letter_id)
            except Exception:
                uow.rollback()
                raise
        return letter

    def get_pending_reviews(self, user_id: str, offset: int = 0, limit: int = 50) -> list[Letter]:
        return self._letter_repo.list_by_status(LetterStatus.PENDING_REVIEW, offset, limit)

    def get_in_review(self, user_id: str, offset: int = 0, limit: int = 50) -> list[Letter]:
        return self._letter_repo.list_by_status(LetterStatus.IN_REVIEW, offset, limit)

    def _get_letter(self, letter_id: str) -> Letter:
        from app.application.letters.letter_service import LetterNotFoundError

        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise LetterNotFoundError(letter_id)
        return letter

    def _persist_events(self, events: list[DomainEvent]) -> None:
        for event in events:
            self._audit_repo.append(event)
