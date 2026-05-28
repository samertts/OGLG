from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.letters.aggregate import LetterAggregate
from app.domain.letters.enums import (
    ArchiveStatus,
    LetterClassification,
    LetterPriority,
    LetterStatus,
    LetterType,
)
from app.domain.letters.events import DomainEvent, EventType
from app.domain.letters.interfaces import (
    AttachmentRepository,
    AuditRepository,
    LetterRepository,
    UnitOfWork,
)
from app.domain.letters.value_objects import (
    Attachment,
)
from app.infrastructure.letters.models import (
    ORMAttachment,
    ORMAuditEvent,
    ORMLetter,
    ORMLetterNumber,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: Session) -> None:
        self._session = session
        self._closed = False

    def commit(self) -> None:
        if not self._closed:
            try:
                self._session.commit()
            except Exception:
                self._session.rollback()
                raise

    def rollback(self) -> None:
        if not self._closed:
            self._session.rollback()

    def flush(self) -> None:
        self._session.flush()

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._session.close()

    def __enter__(self) -> UnitOfWork:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        try:
            if exc_type is not None:
                self.rollback()
            else:
                self.commit()
        finally:
            self.close()


class SqlAlchemyLetterRepository(LetterRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, letter: LetterAggregate) -> None:
        orm = self._to_orm(letter)
        self._session.merge(orm)
        self._save_attachments(letter)
        self._save_reviews(letter)
        self._save_delivery(letter)
        self._save_routing(letter)

    def get_by_id(self, letter_id: str) -> LetterAggregate | None:
        orm = self._session.get(ORMLetter, letter_id)
        if orm is None:
            return None
        return self._from_orm(orm)

    def get_by_number(self, number: str) -> LetterAggregate | None:
        stmt = select(ORMLetter).where(ORMLetter.number == number)
        orm = self._session.execute(stmt).scalar_one_or_none()
        if orm is None:
            return None
        return self._from_orm(orm)

    def delete(self, letter_id: str) -> None:
        stmt = delete(ORMLetter).where(ORMLetter.id == letter_id)
        self._session.execute(stmt)

    def list_by_department(self, department_id: str, offset: int = 0, limit: int = 50) -> list[LetterAggregate]:
        stmt = (
            select(ORMLetter)
            .where(ORMLetter.department_id == department_id)
            .order_by(ORMLetter.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        orms = self._session.execute(stmt).scalars().all()
        return [self._from_orm(o) for o in orms]

    def list_by_status(self, status: LetterStatus, offset: int = 0, limit: int = 50) -> list[LetterAggregate]:
        stmt = (
            select(ORMLetter)
            .where(ORMLetter.status == status.value)
            .order_by(ORMLetter.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        orms = self._session.execute(stmt).scalars().all()
        return [self._from_orm(o) for o in orms]

    def list_by_date_range(self, start: datetime, end: datetime, offset: int = 0, limit: int = 50) -> list[LetterAggregate]:
        stmt = (
            select(ORMLetter)
            .where(ORMLetter.created_at >= start, ORMLetter.created_at <= end)
            .order_by(ORMLetter.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        orms = self._session.execute(stmt).scalars().all()
        return [self._from_orm(o) for o in orms]

    def count_by_department(self, department_id: str) -> int:
        stmt = select(ORMLetter).where(ORMLetter.department_id == department_id)
        return len(self._session.execute(stmt).scalars().all())

    def count_by_status(self, status: LetterStatus) -> int:
        stmt = select(ORMLetter).where(ORMLetter.status == status.value)
        return len(self._session.execute(stmt).scalars().all())

    def _to_orm(self, letter: LetterAggregate) -> ORMLetter:
        return ORMLetter(
            id=letter.id,
            letter_type=letter.letter_type.value,
            status=letter.status.value,
            archive_status=letter.archive_status.value,
            number=letter.number,
            subject=letter.subject,
            body=letter.body,
            sender_id=letter.sender_id,
            sender_name=letter.sender_name,
            sender_department=letter.sender_department,
            recipient_id=letter.recipient_id,
            recipient_name=letter.recipient_name,
            recipient_department=letter.recipient_department,
            recipient_address=letter.recipient_address,
            priority=letter.priority.value,
            classification=letter.classification.value,
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
        )

    def _from_orm(self, orm: ORMLetter) -> LetterAggregate:
        letter = LetterAggregate(
            id=orm.id,
            letter_type=LetterType(orm.letter_type),
            status=LetterStatus(orm.status),
            archive_status=ArchiveStatus(orm.archive_status),
            number=orm.number,
            subject=orm.subject,
            body=orm.body,
            sender_id=orm.sender_id,
            sender_name=orm.sender_name,
            sender_department=orm.sender_department,
            recipient_id=orm.recipient_id,
            recipient_name=orm.recipient_name,
            recipient_department=orm.recipient_department,
            recipient_address=orm.recipient_address,
            priority=LetterPriority(orm.priority),
            classification=LetterClassification(orm.classification),
            department_id=orm.department_id,
            reference_number=orm.reference_number,
            language=orm.language,
            created_by_id=orm.created_by_id,
            created_at=orm.created_at,
            updated_by_id=orm.updated_by_id,
            updated_at=orm.updated_at,
            is_archived=orm.is_archived,
            archived_at=orm.archived_at,
            archived_by_id=orm.archived_by_id,
            deleted_at=orm.deleted_at,
            deleted_by_id=orm.deleted_by_id,
            version=orm.version,
        )
        return letter

    def _save_attachments(self, letter: LetterAggregate) -> None:
        for att in letter.attachments:
            orm_att = ORMAttachment(
                id=att.id,
                letter_id=letter.id,
                filename=att.filename,
                original_name=att.original_name,
                mime_type=att.mime_type,
                file_size=att.file_size,
                extension=att.extension,
                sha256_hash=att.sha256_hash,
                storage_path=att.storage_path,
                uploaded_at=att.uploaded_at,
                uploaded_by=att.uploaded_by,
                description=att.description,
            )
            self._session.merge(orm_att)

    def _save_reviews(self, letter: LetterAggregate) -> None:
        pass

    def _save_delivery(self, letter: LetterAggregate) -> None:
        pass

    def _save_routing(self, letter: LetterAggregate) -> None:
        pass


class SqlAlchemyAuditRepository(AuditRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def append(self, event: DomainEvent) -> None:
        orm = ORMAuditEvent(
            id=str(uuid.uuid4()),
            event_id=event.event_id,
            event_type=event.event_type.name,
            letter_id=event.aggregate_id,
            user_id=event.user_id,
            timestamp=event.timestamp,
            data_json=json.dumps(event.data, default=str),
        )
        self._session.add(orm)

    def get_events_for_letter(self, letter_id: str) -> list[DomainEvent]:
        stmt = (
            select(ORMAuditEvent)
            .where(ORMAuditEvent.letter_id == letter_id)
            .order_by(ORMAuditEvent.timestamp.asc())
        )
        orms = self._session.execute(stmt).scalars().all()
        return [self._orm_to_event(o) for o in orms]

    def get_events_by_user(self, user_id: str, limit: int = 50) -> list[DomainEvent]:
        stmt = (
            select(ORMAuditEvent)
            .where(ORMAuditEvent.user_id == user_id)
            .order_by(ORMAuditEvent.timestamp.desc())
            .limit(limit)
        )
        orms = self._session.execute(stmt).scalars().all()
        return [self._orm_to_event(o) for o in orms]

    def _orm_to_event(self, orm: ORMAuditEvent) -> DomainEvent:
        return DomainEvent(
            event_id=orm.event_id,
            event_type=EventType[orm.event_type],
            aggregate_id=orm.letter_id,
            timestamp=orm.timestamp,
            user_id=orm.user_id,
            data=json.loads(orm.data_json) if orm.data_json else {},
        )


class SqlAlchemyAttachmentRepository(AttachmentRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, attachment: Attachment) -> None:
        orm = ORMAttachment(
            id=attachment.id,
            letter_id="",
            filename=attachment.filename,
            original_name=attachment.original_name,
            mime_type=attachment.mime_type,
            file_size=attachment.file_size,
            extension=attachment.extension,
            sha256_hash=attachment.sha256_hash,
            storage_path=attachment.storage_path,
            uploaded_at=attachment.uploaded_at,
            uploaded_by=attachment.uploaded_by,
            description=attachment.description,
        )
        self._session.add(orm)

    def get_by_id(self, attachment_id: str) -> Attachment | None:
        orm = self._session.get(ORMAttachment, attachment_id)
        if orm is None:
            return None
        return self._orm_to_attachment(orm)

    def get_by_hash(self, sha256_hash: str) -> Attachment | None:
        stmt = select(ORMAttachment).where(ORMAttachment.sha256_hash == sha256_hash)
        orm = self._session.execute(stmt).scalar_one_or_none()
        if orm is None:
            return None
        return self._orm_to_attachment(orm)

    def list_by_letter(self, letter_id: str) -> list[Attachment]:
        stmt = select(ORMAttachment).where(ORMAttachment.letter_id == letter_id)
        orms = self._session.execute(stmt).scalars().all()
        return [self._orm_to_attachment(o) for o in orms]

    def delete(self, attachment_id: str) -> None:
        stmt = delete(ORMAttachment).where(ORMAttachment.id == attachment_id)
        self._session.execute(stmt)

    def _orm_to_attachment(self, orm: ORMAttachment) -> Attachment:
        return Attachment(
            id=orm.id,
            filename=orm.filename,
            original_name=orm.original_name,
            mime_type=orm.mime_type,
            file_size=orm.file_size,
            extension=orm.extension,
            sha256_hash=orm.sha256_hash,
            storage_path=orm.storage_path,
            uploaded_at=orm.uploaded_at,
            uploaded_by=orm.uploaded_by,
            description=orm.description or "",
        )


class SqlAlchemyNumberSequenceProvider:
    def __init__(self, session: Session) -> None:
        self._session = session

    def next_sequence(self, department_code: str, year: int, count: int = 1) -> int:
        from sqlalchemy import func

        stmt = (
            select(func.coalesce(func.max(ORMLetterNumber.sequence), 0))
            .where(
                ORMLetterNumber.department_code == department_code,
                ORMLetterNumber.year == year,
            )
        )
        max_seq = self._session.execute(stmt).scalar() or 0
        new_seq = max_seq + 1
        for i in range(count):
            seq = new_seq + i
            number = f"{department_code}-{year}-{seq:06d}"
            orm = ORMLetterNumber(
                id=str(uuid.uuid4()),
                department_code=department_code,
                year=year,
                sequence=seq,
                number=number,
                created_at=datetime.now(),
                is_used=False,
            )
            self._session.add(orm)
        return new_seq
