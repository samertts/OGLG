"""Integration tests for SQLAlchemy repository implementations.

Tests all repository CRUD operations using an in-memory SQLite database.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session

from app.core.entities.attachment import Attachment
from app.core.entities.audit_entry import AuditEntry
from app.core.entities.backup_log import BackupLog
from app.core.entities.department import Department
from app.core.entities.letter import Letter
from app.core.entities.user import User
from app.core.enums import BackupType, LetterStatus, Priority, UserRole
from app.database.repositories import (
    SQLAlchemyAttachmentRepository,
    SQLAlchemyAuditRepository,
    SQLAlchemyBackupRepository,
    SQLAlchemyDepartmentRepository,
    SQLAlchemyLetterRepository,
    SQLAlchemyUserRepository,
)


class TestDepartmentRepository:
    def test_save_and_find(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyDepartmentRepository(in_memory_session)
        dept = Department(id=uuid4(), name="Health Ministry", code="HM")
        saved = repo.save(dept)
        assert saved.id == dept.id

        found = repo.find_by_id(dept.id)
        assert found is not None
        assert found.name == "Health Ministry"

    def test_find_by_code(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyDepartmentRepository(in_memory_session)
        dept = Department(id=uuid4(), name="Finance", code="FIN")
        repo.save(dept)

        found = repo.find_by_code("FIN")
        assert found is not None
        assert found.id == dept.id

    def test_find_all(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyDepartmentRepository(in_memory_session)
        repo.save(Department(id=uuid4(), name="A", code="A"))
        repo.save(Department(id=uuid4(), name="B", code="B"))
        all_depts = repo.find_all()
        assert len(all_depts) >= 2


class TestUserRepository:
    def test_save_and_find(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyUserRepository(in_memory_session)
        user = User(
            id=uuid4(),
            username="admin",
            full_name="Admin User",
            role=UserRole.ADMIN,
            password_hash="abc123",
        )
        saved = repo.save(user)
        assert saved.id == user.id

        found = repo.find_by_id(user.id)
        assert found is not None
        assert found.username == "admin"

    def test_find_by_username(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyUserRepository(in_memory_session)
        user = User(id=uuid4(), username="operator", full_name="Op", role=UserRole.EDITOR, password_hash="x")
        repo.save(user)
        found = repo.find_by_username("operator")
        assert found is not None


class TestLetterRepository:
    def test_save_and_find(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyLetterRepository(in_memory_session)
        letter = Letter(
            id=uuid4(),
            number="2024-0001",
            subject="Test",
            body="Body",
            sender_name="Sender",
            recipient_name="Recipient",
            content_hash="a" * 64,
        )
        saved = repo.save(letter)
        assert saved.id == letter.id

        found = repo.find_by_id(letter.id)
        assert found is not None
        assert found.subject == "Test"

    def test_find_by_number(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyLetterRepository(in_memory_session)
        letter = Letter(
            id=uuid4(),
            number="2024-0001",
            subject="Test",
            body="Body",
            sender_name="S",
            recipient_name="R",
            content_hash="a" * 64,
        )
        repo.save(letter)
        found = repo.find_by_number("2024-0001")
        assert found is not None

    def test_next_sequence(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyLetterRepository(in_memory_session)
        seq = repo.next_sequence_for_year(2024)
        assert seq >= 1


class TestAttachmentRepository:
    def test_save_and_find_by_letter(self, in_memory_session: Session) -> None:
        letter_repo = SQLAlchemyLetterRepository(in_memory_session)
        letter = Letter(
            id=uuid4(),
            number="2024-0001",
            subject="Test",
            body="Body",
            sender_name="S",
            recipient_name="R",
            content_hash="a" * 64,
        )
        letter_repo.save(letter)

        repo = SQLAlchemyAttachmentRepository(in_memory_session)
        att = Attachment(
            id=uuid4(),
            letter_id=letter.id,
            filename="doc.pdf",
            original_name="doc.pdf",
            file_path="/tmp/doc.pdf",
            mime_type="application/pdf",
            size_bytes=100,
            hash_sha256="b" * 64,
        )
        repo.save(att)

        found = repo.find_by_letter(letter.id)
        assert len(found) == 1


class TestAuditRepository:
    def test_append_and_find(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyAuditRepository(in_memory_session)
        entry = AuditEntry(
            id=uuid4(),
            user_id=uuid4(),
            action="CREATE",
            entity_type="Letter",
            entity_id=str(uuid4()),
            result="success",
        )
        saved = repo.append(entry)
        assert saved.id == entry.id

        found = repo.find_by_id(entry.id)
        assert found is not None

    def test_append_only(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyAuditRepository(in_memory_session)
        e1 = AuditEntry(id=uuid4(), user_id=uuid4(), action="A", entity_type="T", entity_id="1")
        e2 = AuditEntry(id=uuid4(), user_id=uuid4(), action="B", entity_type="T", entity_id="1")
        repo.append(e1)
        repo.append(e2)
        assert repo.count_all() >= 2


class TestBackupRepository:
    def test_append_and_find_latest(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyBackupRepository(in_memory_session)
        entry = BackupLog(
            id=uuid4(),
            backup_path="/tmp/backup.db",
            size_bytes=1000,
            hash_sha256="a" * 64,
            type=BackupType.MANUAL,
            created_by_id=uuid4(),
        )
        repo.append(entry)

        latest = repo.find_latest()
        assert latest is not None
        assert latest.id == entry.id

    def test_mark_restored(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyBackupRepository(in_memory_session)
        entry = BackupLog(
            id=uuid4(),
            backup_path="/tmp/backup.db",
            size_bytes=1000,
            hash_sha256="a" * 64,
            type=BackupType.MANUAL,
            created_by_id=uuid4(),
        )
        repo.append(entry)
        user_id = uuid4()
        repo.mark_restored(entry.id, user_id)

        found = repo.find_by_id(entry.id)
        assert found is not None
        assert found.restored_at is not None
