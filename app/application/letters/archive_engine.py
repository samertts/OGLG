from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger

from app.domain.letters.enums import ArchiveStatus, LetterStatus
from app.domain.letters.interfaces import AuditRepository, LetterRepository


class ArchiveEngine:
    def __init__(
        self,
        letter_repo: LetterRepository,
        audit_repo: AuditRepository,
        uow_factory: Any,
        archive_dir: str = "",
    ) -> None:
        self._letter_repo = letter_repo
        self._audit_repo = audit_repo
        self._uow_factory = uow_factory
        self._archive_dir = archive_dir

    def archive(self, letter_id: str, user_id: str, reason: str = "") -> dict[str, Any]:

        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {letter_id}")
        letter.archive(user_id, reason)
        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()
        logger.info(f"Archived letter: {letter_id}")
        return {"letter_id": letter_id, "archived_at": datetime.now().isoformat(), "status": "archived"}

    def restore(self, letter_id: str, user_id: str, reason: str = "") -> dict[str, Any]:
        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {letter_id}")
        letter.restore(user_id, reason)
        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()
        logger.info(f"Restored letter: {letter_id}")
        return {"letter_id": letter_id, "restored_at": datetime.now().isoformat(), "status": "restored"}

    def soft_delete(self, letter_id: str, user_id: str, reason: str = "") -> dict[str, Any]:
        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            raise ValueError(f"Letter not found: {letter_id}")
        letter.soft_delete(user_id, reason)
        with self._uow_factory() as uow:
            self._letter_repo.save(letter)
            for event in letter.pop_events():
                self._audit_repo.append(event)
            uow.commit()
        logger.info(f"Soft deleted letter: {letter_id}")
        return {"letter_id": letter_id, "deleted_at": datetime.now().isoformat(), "status": "soft_deleted"}

    def list_archived(self, department_id: str | None = None, offset: int = 0, limit: int = 50) -> list[dict[str, Any]]:
        letters = self._letter_repo.list_by_status(LetterStatus.ARCHIVED, offset, limit)
        results = []
        for letter in letters:
            if department_id and letter.department_id != department_id:
                continue
            results.append({
                "id": letter.id,
                "number": letter.number,
                "subject": letter.subject,
                "sender_name": letter.sender_name,
                "archived_at": letter.archived_at.isoformat() if letter.archived_at else "",
                "archived_by_id": letter.archived_by_id,
            })
        return results

    def list_deleted(self, department_id: str | None = None, offset: int = 0, limit: int = 50) -> list[dict[str, Any]]:
        letters = self._letter_repo.list_by_status(LetterStatus.DELETED, offset, limit)
        results = []
        for letter in letters:
            if department_id and letter.department_id != department_id:
                continue
            results.append({
                "id": letter.id,
                "number": letter.number,
                "subject": letter.subject,
                "deleted_at": letter.deleted_at.isoformat() if letter.deleted_at else "",
                "deleted_by_id": letter.deleted_by_id,
            })
        return results

    def count_by_status(self, status: ArchiveStatus) -> int:
        status_map = {
            ArchiveStatus.ACTIVE: LetterStatus.DRAFT,
            ArchiveStatus.ARCHIVED: LetterStatus.ARCHIVED,
            ArchiveStatus.SOFT_DELETED: LetterStatus.DELETED,
        }
        letter_status = status_map.get(status)
        if letter_status:
            return self._letter_repo.count_by_status(letter_status)
        return 0

    def validate_archive_integrity(self, letter_id: str) -> dict[str, Any]:
        letter = self._letter_repo.get_by_id(letter_id)
        if letter is None:
            return {"valid": False, "reason": "not_found"}
        issues = []
        if letter.is_archived and not letter.archived_at:
            issues.append("Missing archived_at timestamp")
        if letter.is_archived and not letter.archived_by_id:
            issues.append("Missing archived_by user")
        if letter.archive_status == ArchiveStatus.SOFT_DELETED and not letter.deleted_at:
            issues.append("Missing deleted_at timestamp for soft-deleted letter")
        if letter.archive_status == ArchiveStatus.SOFT_DELETED and not letter.deleted_by_id:
            issues.append("Missing deleted_by_id for soft-deleted letter")
        return {"valid": len(issues) == 0, "issues": issues, "archive_status": letter.archive_status.value}
