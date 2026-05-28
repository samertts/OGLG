from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.letters.enums import (
    ArchiveStatus,
    LetterClassification,
    LetterPriority,
    LetterStatus,
    LetterType,
)


@dataclass
class CreateLetterDTO:
    letter_type: LetterType
    subject: str
    body: str
    sender_id: str
    sender_name: str
    sender_department: str
    department_id: str
    created_by_id: str
    priority: LetterPriority = LetterPriority.NORMAL
    classification: LetterClassification = LetterClassification.INTERNAL
    language: str = "AR"
    recipient_name: str = ""
    recipient_department: str = ""
    recipient_address: str = ""
    recipient_id: str | None = None
    reference_number: str | None = None


@dataclass
class EditLetterDTO:
    letter_id: str
    user_id: str
    subject: str | None = None
    body: str | None = None
    priority: LetterPriority | None = None
    classification: LetterClassification | None = None
    recipient_name: str | None = None
    recipient_department: str | None = None
    recipient_address: str | None = None


@dataclass
class ReviewLetterDTO:
    letter_id: str
    reviewer_id: str
    user_id: str
    action: str
    notes: str = ""
    reason: str = ""


@dataclass
class ArchiveLetterDTO:
    letter_id: str
    user_id: str
    reason: str = ""


@dataclass
class SearchLetterDTO:
    query: str = ""
    status: LetterStatus | None = None
    letter_type: LetterType | None = None
    priority: LetterPriority | None = None
    classification: LetterClassification | None = None
    department_id: str | None = None
    sender_id: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    offset: int = 0
    limit: int = 50


@dataclass
class NumberRequestDTO:
    department_code: str
    year: int | None = None


@dataclass
class AttachmentUploadDTO:
    letter_id: str
    filepath: str
    original_name: str
    uploaded_by: str
    description: str = ""


@dataclass
class LetterResultDTO:
    id: str
    letter_type: LetterType
    status: LetterStatus
    archive_status: ArchiveStatus
    number: str | None
    subject: str
    body: str
    sender_id: str
    sender_name: str
    sender_department: str
    recipient_id: str | None
    recipient_name: str
    recipient_department: str
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
    version: int
    attachment_count: int = 0
    review_count: int = 0
    current_reviewer: str | None = None

    @staticmethod
    def from_aggregate(letter: Any) -> LetterResultDTO:
        return LetterResultDTO(
            id=letter.id,
            letter_type=letter.letter_type,
            status=letter.status,
            archive_status=letter.archive_status,
            number=letter.number,
            subject=letter.subject,
            body=letter.body,
            sender_id=letter.sender_id,
            sender_name=letter.sender_name,
            sender_department=letter.sender_department,
            recipient_id=letter.recipient_id,
            recipient_name=letter.recipient_name,
            recipient_department=letter.recipient_department,
            priority=letter.priority,
            classification=letter.classification,
            department_id=letter.department_id,
            reference_number=letter.reference_number,
            language=letter.language,
            created_by_id=letter.created_by_id,
            created_at=letter.created_at,
            updated_by_id=letter.updated_by_id,
            updated_at=letter.updated_at,
            is_archived=letter.is_archived,
            archived_at=letter.archived_at,
            archived_by_id=letter.archived_by_id,
            deleted_at=letter.deleted_at,
            deleted_by_id=letter.deleted_by_id,
            version=letter.version,
            attachment_count=len(letter.attachments),
            review_count=len(letter.reviews),
            current_reviewer=letter.current_reviewer.reviewer_name if letter.current_reviewer else None,
        )


@dataclass
class NumberResultDTO:
    number: str
    prefix: str
    year: int
    sequence: int
    department_code: str


@dataclass
class SearchResultDTO:
    total: int
    offset: int
    limit: int
    results: list[LetterResultDTO]


@dataclass
class AuditEventDTO:
    event_id: str
    event_type: str
    letter_id: str
    user_id: str
    timestamp: datetime
    data: dict[str, Any]
