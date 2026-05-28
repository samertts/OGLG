from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol

from app.domain.letters.archive_state import ArchiveState
from app.domain.letters.attachment import Attachment
from app.domain.letters.events import DomainEvent
from app.domain.letters.letter import LetterType
from app.domain.letters.letter_classification import LetterClassification
from app.domain.letters.letter_priority import LetterPriority
from app.domain.letters.letter_status import LetterStatus


class LetterData(Protocol):
    id: str
    letter_type: LetterType
    status: LetterStatus
    number: str | None
    subject: str
    body: str
    sender_id: str
    sender_name: str
    sender_department: str
    recipient_id: str | None
    recipient_name: str
    recipient_department: str
    recipient_address: str
    priority: LetterPriority
    classification: LetterClassification
    department_id: str
    reference_number: str | None
    language: str
    created_by_id: str
    created_at: datetime
    updated_by_id: str | None
    updated_at: datetime | None
    is_archived: bool
    archived_at: datetime | None
    archived_by_id: str | None
    deleted_at: datetime | None
    deleted_by_id: str | None
    archive_state: ArchiveState
    version: int


class LetterRepository(Protocol):
    def save(self, letter: LetterData) -> None: ...
    def get_by_id(self, letter_id: str) -> LetterData | None: ...
    def get_by_number(self, number: str) -> LetterData | None: ...
    def delete(self, letter_id: str) -> None: ...
    def list_by_department(self, department_id: str, offset: int = 0, limit: int = 50) -> list[LetterData]: ...
    def list_by_status(self, status: LetterStatus, offset: int = 0, limit: int = 50) -> list[LetterData]: ...
    def list_by_date_range(self, start: datetime, end: datetime, offset: int = 0, limit: int = 50) -> list[LetterData]: ...
    def count_by_department(self, department_id: str) -> int: ...
    def count_by_status(self, status: LetterStatus) -> int: ...


class AuditRepository(Protocol):
    def append(self, event: DomainEvent) -> None: ...
    def get_events_for_letter(self, letter_id: str) -> list[DomainEvent]: ...
    def get_events_by_user(self, user_id: str, limit: int = 50) -> list[DomainEvent]: ...


class AttachmentRepository(Protocol):
    def save(self, attachment: Attachment) -> None: ...
    def get_by_id(self, attachment_id: str) -> Attachment | None: ...
    def get_by_hash(self, sha256_hash: str) -> Attachment | None: ...
    def list_by_letter(self, letter_id: str) -> list[Attachment]: ...
    def delete(self, attachment_id: str) -> None: ...


class UnitOfWork(Protocol):
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def flush(self) -> None: ...
    def __enter__(self) -> UnitOfWork: ...
    def __exit__(self, *args: Any) -> None: ...
