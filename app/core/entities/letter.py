from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.core.enums import LanguageTag, LetterStatus, Priority
from app.core.value_objects.letter_number import LetterNumber


@dataclass
class Letter:
    id: UUID = field(default_factory=uuid4)
    number: str = ""
    subject: str = ""
    body: str = ""
    sender_name: str = ""
    sender_title: str = ""
    recipient_name: str = ""
    recipient_title: str = ""
    recipient_dept: str = ""
    department_id: UUID | None = None
    priority: Priority = Priority.NORMAL
    status: LetterStatus = LetterStatus.DRAFT
    reference_number: str | None = None
    language: LanguageTag = LanguageTag.AR

    created_by_id: UUID | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_by_id: UUID | None = None
    updated_at: datetime | None = None

    is_archived: bool = False
    archived_at: datetime | None = None
    archived_by_id: UUID | None = None

    content_hash: str = ""
    version: int = 1

    is_deleted: bool = False
    deleted_at: datetime | None = None
    deleted_by_id: UUID | None = None

    @property
    def formatted_number(self) -> str:
        try:
            return LetterNumber.parse(self.number).format()
        except (ValueError, AttributeError):
            return self.number

    def archive(self, user_id: UUID) -> None:
        self.status = LetterStatus.ARCHIVED
        self.is_archived = True
        self.archived_at = datetime.now()
        self.archived_by_id = user_id

    def restore(self) -> None:
        self.status = LetterStatus.SENT
        self.is_archived = False
        self.archived_at = None
        self.archived_by_id = None

    def soft_delete(self, user_id: UUID) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now()
        self.deleted_by_id = user_id

    def mark_updated(self, user_id: UUID) -> None:
        self.updated_at = datetime.now()
        self.updated_by_id = user_id
        self.version += 1
