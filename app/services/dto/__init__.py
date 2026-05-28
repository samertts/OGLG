"""Data Transfer Objects for the Correspondence System."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

T = TypeVar("T")

from app.core.enums import BackupType, LanguageTag, LetterStatus, Priority


@dataclass
class LetterCreateDTO:
    subject: str
    body: str
    sender_name: str
    sender_title: str = ""
    recipient_name: str = ""
    recipient_title: str = ""
    recipient_dept: str = ""
    department_id: UUID | None = None
    priority: Priority = Priority.NORMAL
    language: LanguageTag = LanguageTag.AR
    reference_number: str | None = None
    created_by_id: UUID | None = None


@dataclass
class LetterUpdateDTO:
    subject: str | None = None
    body: str | None = None
    sender_name: str | None = None
    sender_title: str | None = None
    recipient_name: str | None = None
    recipient_title: str | None = None
    recipient_dept: str | None = None
    department_id: UUID | None = None
    priority: Priority | None = None
    language: LanguageTag | None = None
    reference_number: str | None = None
    updated_by_id: UUID | None = None


@dataclass
class LetterResponseDTO:
    id: UUID
    number: str
    subject: str
    body: str
    sender_name: str
    sender_title: str
    recipient_name: str
    recipient_title: str
    recipient_dept: str
    department_id: UUID | None
    priority: Priority
    status: LetterStatus
    reference_number: str | None
    language: LanguageTag
    created_by_id: UUID | None
    created_at: datetime
    updated_by_id: UUID | None
    updated_at: datetime | None
    is_archived: bool
    archived_at: datetime | None
    content_hash: str
    version: int
    is_deleted: bool

    @classmethod
    def from_entity(cls, letter: Letter) -> LetterResponseDTO:  # type: ignore[name-defined]
        return cls(
            id=letter.id,
            number=letter.number,
            subject=letter.subject,
            body=letter.body,
            sender_name=letter.sender_name,
            sender_title=letter.sender_title,
            recipient_name=letter.recipient_name,
            recipient_title=letter.recipient_title,
            recipient_dept=letter.recipient_dept,
            department_id=letter.department_id,
            priority=letter.priority,
            status=letter.status,
            reference_number=letter.reference_number,
            language=letter.language,
            created_by_id=letter.created_by_id,
            created_at=letter.created_at,
            updated_by_id=letter.updated_by_id,
            updated_at=letter.updated_at,
            is_archived=letter.is_archived,
            archived_at=letter.archived_at,
            content_hash=letter.content_hash,
            version=letter.version,
            is_deleted=letter.is_deleted,
        )


@dataclass
class AuditEntryCreateDTO:
    user_id: UUID | None
    action: str
    entity_type: str
    entity_id: str
    details_json: str = "{}"
    ip_address: str | None = None
    result: str = "success"


@dataclass
class AuditEntryResponseDTO:
    id: UUID
    timestamp: datetime
    user_id: UUID | None
    action: str
    entity_type: str
    entity_id: str
    details_json: str
    ip_address: str | None
    result: str

    @classmethod
    def from_entity(cls, entry: AuditEntry) -> AuditEntryResponseDTO:  # type: ignore[name-defined]
        return cls(
            id=entry.id,
            timestamp=entry.timestamp,
            user_id=entry.user_id,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            details_json=entry.details_json,
            ip_address=entry.ip_address,
            result=entry.result,
        )


@dataclass
class BackupCreateDTO:
    backup_path: str
    size_bytes: int
    hash_sha256: str
    type: BackupType = BackupType.MANUAL
    created_by_id: UUID | None = None
    notes: str | None = None


@dataclass
class BackupResponseDTO:
    id: UUID
    backup_path: str
    size_bytes: int
    hash_sha256: str
    type: BackupType
    created_by_id: UUID | None
    created_at: datetime
    restored_at: datetime | None
    restored_by_id: UUID | None
    notes: str | None

    @classmethod
    def from_entity(cls, entry: BackupLog) -> BackupResponseDTO:  # type: ignore[name-defined]
        return cls(
            id=entry.id,
            backup_path=entry.backup_path,
            size_bytes=entry.size_bytes,
            hash_sha256=entry.hash_sha256,
            type=entry.type,
            created_by_id=entry.created_by_id,
            created_at=entry.created_at,
            restored_at=entry.restored_at,
            restored_by_id=entry.restored_by_id,
            notes=entry.notes,
        )


@dataclass
class DepartmentCreateDTO:
    name: str
    code: str
    parent_id: UUID | None = None


@dataclass
class UserCreateDTO:
    username: str
    full_name: str
    password_hash: str
    title: str = ""
    email: str | None = None
    role: str = "VIEWER"
    department_id: UUID | None = None


@dataclass
class PaginatedResult(Generic[T]):
    items: list[T]
    total: int
    offset: int
    limit: int
