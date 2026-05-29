from __future__ import annotations

from typing import Any

from loguru import logger

from app.domain.letters.events import DomainEvent
from app.domain.letters.interfaces import AuditRepository, LetterRepository
from app.domain.letters.letter import Letter
from app.domain.letters.letter_classification import LetterClassification
from app.domain.letters.letter_priority import LetterPriority
from app.domain.letters.letter_status import LetterStatus


class LetterServiceError(Exception):
    pass


class LetterNotFoundError(LetterServiceError):
    def __init__(self, letter_id: str) -> None:
        self.letter_id = letter_id
        super().__init__(f"Letter not found: {letter_id}")


class LetterNotEditableError(LetterServiceError):
    def __init__(self, letter_id: str, status: str) -> None:
        super().__init__(f"Letter {letter_id} is not editable in status: {status}")


class LetterValidationError(LetterServiceError):
    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        self.errors = errors or []
        super().__init__(message)


class LetterService:
    def __init__(
        self,
        letter_repo: LetterRepository,
        audit_repo: AuditRepository,
        uow_factory: Any,
    ) -> None:
        self._letter_repo = letter_repo
        self._audit_repo = audit_repo
        self._uow_factory = uow_factory

    def create_draft(
        self,
        letter_type: str,
        subject: str,
        body: str,
        sender_id: str,
        sender_name: str,
        sender_department: str,
        department_id: str,
        created_by_id: str,
        priority: LetterPriority = LetterPriority.NORMAL,
        classification: LetterClassification = LetterClassification.INTERNAL,
        language: str = "AR",
        recipient_name: str = "",
        recipient_department: str = "",
        recipient_address: str = "",
        recipient_id: str | None = None,
        reference_number: str | None = None,
    ) -> Letter:
        letter = Letter.create(
            letter_type=letter_type,
            subject=subject,
            body=body,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_department=sender_department,
            department_id=department_id,
            created_by_id=created_by_id,
            priority=priority,
            classification=classification,
            language=language,
            recipient_name=recipient_name,
            recipient_department=recipient_department,
            recipient_address=recipient_address,
            recipient_id=recipient_id,
            reference_number=reference_number,
        )
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter, letter.pop_events())
                uow.commit()
                logger.info("Created letter {}", letter.id)
            except Exception:
                uow.rollback()
                logger.error("Failed to create letter: {}", exc_info=True)
                raise
        return letter

    def edit_draft(
        self,
        letter_id: str,
        user_id: str,
        subject: str | None = None,
        body: str | None = None,
        priority: LetterPriority | None = None,
        classification: LetterClassification | None = None,
        recipient_name: str | None = None,
        recipient_department: str | None = None,
        recipient_address: str | None = None,
    ) -> Letter:
        letter = self._get_letter(letter_id)
        try:
            letter.edit(
                user_id=user_id,
                subject=subject,
                body=body,
                priority=priority,
                classification=classification,
                recipient_name=recipient_name,
                recipient_department=recipient_department,
                recipient_address=recipient_address,
            )
        except ValueError as e:
            raise LetterNotEditableError(letter_id, letter.status.value) from e
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter, letter.pop_events())
                uow.commit()
                logger.info("Edited letter {}", letter_id)
            except Exception:
                uow.rollback()
                raise
        return letter

    def submit_for_review(self, letter_id: str, user_id: str) -> Letter:
        letter = self._get_letter(letter_id)
        try:
            letter.submit_for_review(user_id)
        except Exception as e:
            raise LetterServiceError(f"Cannot submit letter {letter_id}: {e}") from e
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter, letter.pop_events())
                uow.commit()
                logger.info("Submitted letter {} for review", letter_id)
            except Exception:
                uow.rollback()
                raise
        return letter

    def cancel_letter(self, letter_id: str, user_id: str, reason: str = "") -> Letter:
        letter = self._get_letter(letter_id)
        try:
            letter.soft_delete(user_id, reason)
        except Exception as e:
            raise LetterServiceError(f"Cannot cancel letter {letter_id}: {e}") from e
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter, letter.pop_events())
                uow.commit()
                logger.info("Cancelled letter {}: {}", letter_id, reason)
            except Exception:
                uow.rollback()
                raise
        return letter

    def get_letter(self, letter_id: str) -> Letter | None:
        return self._letter_repo.get_by_id(letter_id)

    def list_by_status(
        self, status: LetterStatus, offset: int = 0, limit: int = 50
    ) -> list[Letter]:
        return self._letter_repo.list_by_status(status, offset, limit)

    def list_by_department(
        self, department_id: str, offset: int = 0, limit: int = 50
    ) -> list[Letter]:
        return self._letter_repo.list_by_department(department_id, offset, limit)

    def count_by_status(self, status: LetterStatus) -> int:
        return self._letter_repo.count_by_status(status)

    def count_by_department(self, department_id: str) -> int:
        return self._letter_repo.count_by_department(department_id)

    def _get_letter(self, letter_id: str) -> Letter:
        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise LetterNotFoundError(letter_id)
        return letter

    def _persist_events(self, letter: Letter, events: list[DomainEvent]) -> None:
        for event in events:
            self._audit_repo.append(event)
