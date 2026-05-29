from __future__ import annotations

from typing import Any

from loguru import logger

from app.domain.letters.archive_state import ArchiveState
from app.domain.letters.events import DomainEvent, EventType
from app.domain.letters.interfaces import AuditRepository, LetterRepository
from app.domain.letters.letter import Letter
from app.domain.letters.letter_status import LetterStatus
from app.domain.letters.state_machine import (
    validate_lifecycle_transition,
)


class RecoveryServiceError(Exception):
    pass


class RecoveryService:
    def __init__(
        self,
        letter_repo: LetterRepository,
        audit_repo: AuditRepository,
        uow_factory: Any,
    ) -> None:
        self._letter_repo = letter_repo
        self._audit_repo = audit_repo
        self._uow_factory = uow_factory

    def recover_failed_transition(
        self, letter_id: str, user_id: str, target_status: LetterStatus
    ) -> Letter:
        letter = self._get_letter(letter_id)
        try:
            validate_lifecycle_transition(letter.status, target_status)
        except Exception as e:
            raise RecoveryServiceError(
                f"Cannot recover letter {letter_id} to {target_status.value}: {e}"
            ) from e
        letter.status = target_status
        letter.updated_by_id = user_id
        from datetime import datetime
        letter.updated_at = datetime.now()
        letter.version += 1
        self._generate_recovery_event(letter, user_id, target_status)
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter.pop_events())
                uow.commit()
                logger.info("Recovered letter {} to {}", letter_id, target_status.value)
            except Exception:
                uow.rollback()
                raise
        return letter

    def retry_operation(self, letter_id: str, operation: str, user_id: str, **kwargs: Any) -> Letter:
        letter = self._get_letter(letter_id)
        retryable = {
            "submit": self._retry_submit,
            "approve": self._retry_approve,
            "archive": self._retry_archive,
        }
        handler = retryable.get(operation)
        if handler is None:
            raise RecoveryServiceError(f"Unknown retry operation: {operation}")
        try:
            handler(letter, user_id, **kwargs)
        except Exception as e:
            raise RecoveryServiceError(f"Retry failed for {operation} on {letter_id}: {e}") from e
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter.pop_events())
                uow.commit()
                logger.info("Retried {} for letter {}", operation, letter_id)
            except Exception:
                uow.rollback()
                raise
        return letter

    def validate_consistency(self, letter_id: str) -> list[str]:
        letter = self._get_letter(letter_id)
        issues: list[str] = []
        if letter.is_archived and letter.archive_state != ArchiveState.ARCHIVED:
            issues.append("is_archived=True but archive_state is not ARCHIVED")
        if not letter.is_archived and letter.archive_state == ArchiveState.ARCHIVED:
            issues.append("is_archived=False but archive_state is ARCHIVED")
        if letter.status == LetterStatus.ARCHIVED and letter.archive_state != ArchiveState.ARCHIVED:
            issues.append("status=ARCHIVED but archive_state is not ARCHIVED")
        if letter.status == LetterStatus.DELETED and letter.archive_state != ArchiveState.SOFT_DELETED:
            issues.append("status=DELETED but archive_state is not SOFT_DELETED")
        if letter.status == LetterStatus.DRAFT and letter.version > 1 and not letter._events:
            issues.append("DRAFT with version>1 and no pending events")
        return issues

    def resolve_conflict(
        self, letter_id: str, user_id: str, consistent_status: LetterStatus, consistent_archive: ArchiveState
    ) -> Letter:
        letter = self._get_letter(letter_id)
        issues = self.validate_consistency(letter_id)
        if not issues:
            raise RecoveryServiceError(f"Letter {letter_id} has no consistency issues")
        letter.status = consistent_status
        letter.archive_state = consistent_archive
        letter.is_archived = consistent_archive == ArchiveState.ARCHIVED
        letter.updated_by_id = user_id
        from datetime import datetime
        letter.updated_at = datetime.now()
        letter.version += 1
        self._generate_recovery_event(letter, user_id, consistent_status)
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter.pop_events())
                uow.commit()
                logger.info("Resolved conflict for letter {} to status {}", letter_id, consistent_status.value)
            except Exception:
                uow.rollback()
                raise
        return letter

    def _retry_submit(self, letter: Letter, user_id: str, **kwargs: Any) -> None:
        letter.submit_for_review(user_id)

    def _retry_approve(self, letter: Letter, user_id: str, **kwargs: Any) -> None:
        reviewer_id = kwargs.get("reviewer_id", user_id)
        notes = kwargs.get("notes", "")
        letter.approve(user_id, reviewer_id, notes)

    def _retry_archive(self, letter: Letter, user_id: str, **kwargs: Any) -> None:
        reason = kwargs.get("reason", "")
        letter.archive(user_id, reason)

    def _get_letter(self, letter_id: str) -> Letter:
        from app.application.letters.letter_service import LetterNotFoundError

        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise LetterNotFoundError(letter_id)
        return letter

    def _generate_recovery_event(
        self, letter: Letter, user_id: str, target_status: LetterStatus
    ) -> None:
        import uuid
        from datetime import datetime

        event = DomainEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LETTER_EXPORTED,
            aggregate_id=letter.id,
            timestamp=datetime.now(),
            user_id=user_id,
            data={
                "action": "RECOVERY",
                "from_status": letter.status.value,
                "to_status": target_status.value,
            },
        )
        letter._events.append(event)

    def _persist_events(self, events: list[DomainEvent]) -> None:
        for event in events:
            self._audit_repo.append(event)
