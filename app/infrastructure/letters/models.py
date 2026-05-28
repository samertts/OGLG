from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


class ORMLetter(Base):
    __tablename__ = "letters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    letter_type = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="DRAFT", index=True)
    archive_status = Column(String(20), nullable=False, default="ACTIVE")
    number = Column(String(30), nullable=True, unique=True, index=True)
    subject = Column(String(500), nullable=False, index=True)
    body = Column(Text, nullable=False)
    sender_id = Column(String(36), nullable=False, index=True)
    sender_name = Column(String(200), nullable=False)
    sender_department = Column(String(200), nullable=False)
    recipient_id = Column(String(36), nullable=True)
    recipient_name = Column(String(200), default="")
    recipient_department = Column(String(200), default="")
    recipient_address = Column(String(500), default="")
    priority = Column(String(20), nullable=False, default="NORMAL", index=True)
    classification = Column(String(20), nullable=False, default="INTERNAL")
    department_id = Column(String(36), nullable=False, index=True)
    reference_number = Column(String(100), nullable=True)
    language = Column(String(5), nullable=False, default="AR")
    created_by_id = Column(String(36), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_by_id = Column(String(36), nullable=True)
    updated_at = Column(DateTime, nullable=True)
    is_archived = Column(Boolean, default=False)
    archived_at = Column(DateTime, nullable=True)
    archived_by_id = Column(String(36), nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(String(36), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    content_hash = Column(String(64), nullable=True)

    attachments = relationship("ORMAttachment", back_populates="letter", cascade="all, delete-orphan", lazy="selectin")
    audit_events = relationship("ORMAuditEvent", back_populates="letter", cascade="all, delete-orphan", lazy="selectin")


class ORMAttachment(Base):
    __tablename__ = "letter_attachments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    letter_id = Column(String(36), ForeignKey("letters.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    extension = Column(String(10), nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)
    storage_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.now)
    uploaded_by = Column(String(36), nullable=False)
    description = Column(Text, default="")
    is_encrypted = Column(Boolean, default=False)

    letter = relationship("ORMLetter", back_populates="attachments")


class ORMAuditEvent(Base):
    __tablename__ = "letter_audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_id = Column(String(36), nullable=False, unique=True)
    event_type = Column(String(50), nullable=False, index=True)
    letter_id = Column(String(36), ForeignKey("letters.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now, index=True)
    data_json = Column(Text, default="{}")

    letter = relationship("ORMLetter", back_populates="audit_events")


class ORMLetterNumber(Base):
    __tablename__ = "letter_numbers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    department_code = Column(String(10), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    number = Column(String(30), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    is_used = Column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("department_code", "year", "sequence", name="uq_dept_year_seq"),
    )


class ORMAttachmentStorage(Base):
    __tablename__ = "attachment_storage"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    attachment_id = Column(String(36), ForeignKey("letter_attachments.id", ondelete="CASCADE"), nullable=False, unique=True)
    file_data = Column(LargeBinary, nullable=False)
    stored_at = Column(DateTime, nullable=False, default=datetime.now)
