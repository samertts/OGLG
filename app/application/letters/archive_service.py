from __future__ import annotations

from typing import Any

from loguru import logger

from app.domain.letters.events import DomainEvent
from app.domain.letters.interfaces import AuditRepository, LetterRepository
from app.domain.letters.letter import Letter
from app.domain.letters.letter_status import LetterStatus


class ArchiveServiceError(Exception):
    pass


class ArchiveService:
    def __init__(
        self,
        letter_repo: LetterRepository,
        audit_repo: AuditRepository,
        uow_factory: Any,
    ) -> None:
        self._letter_repo = letter_repo
        self._audit_repo = audit_repo
        self._uow_factory = uow_factory

    def archive(self, letter_id: str, user_id: str, reason: str = "") -> Letter:
        letter = self._get_letter(letter_id)
        try:
            letter.archive(user_id, reason)
        except Exception as e:
            raise ArchiveServiceError(f"Cannot archive letter {letter_id}: {e}") from e
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter.pop_events())
                uow.commit()
                logger.info("Archived letter {}: {}", letter_id, reason)
            except Exception:
                uow.rollback()
                raise
        return letter

    def restore(self, letter_id: str, user_id: str, reason: str = "") -> Letter:
        letter = self._get_letter(letter_id)
        try:
            letter.restore(user_id, reason)
        except Exception as e:
            raise ArchiveServiceError(f"Cannot restore letter {letter_id}: {e}") from e
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter.pop_events())
                uow.commit()
                logger.info("Restored letter {}: {}", letter_id, reason)
            except Exception:
                uow.rollback()
                raise
        return letter

    def soft_delete(self, letter_id: str, user_id: str, reason: str = "") -> Letter:
        letter = self._get_letter(letter_id)
        try:
            letter.soft_delete(user_id, reason)
        except Exception as e:
            raise ArchiveServiceError(f"Cannot soft-delete letter {letter_id}: {e}") from e
        with self._uow_factory() as uow:
            try:
                self._letter_repo.save(letter)
                self._persist_events(letter.pop_events())
                uow.commit()
                logger.info("Soft-deleted letter {}: {}", letter_id, reason)
            except Exception:
                uow.rollback()
                raise
        return letter

    def list_archived(self, offset: int = 0, limit: int = 50) -> list[Letter]:
        return self._letter_repo.list_by_status(LetterStatus.ARCHIVED, offset, limit)

    def list_deleted(self, offset: int = 0, limit: int = 50) -> list[Letter]:
        return self._letter_repo.list_by_status(LetterStatus.DELETED, offset, limit)

    def count_archived(self) -> int:
        return self._letter_repo.count_by_status(LetterStatus.ARCHIVED)

    def count_deleted(self) -> int:
        return self._letter_repo.count_by_status(LetterStatus.DELETED)

    def _get_letter(self, letter_id: str) -> Letter:
        from app.application.letters.letter_service import LetterNotFoundError

        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise LetterNotFoundError(letter_id)
        return letter

    def _persist_events(self, events: list[DomainEvent]) -> None:
        for event in events:
            self._audit_repo.append(event)
