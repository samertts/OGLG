"""Integration tests for audit and backup services."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.enums import BackupType
from app.database.connection import DatabaseManager
from app.database.models import Base
from app.database.repositories import (
    SQLAlchemyAuditRepository,
    SQLAlchemyBackupRepository,
)
from app.services.audit_service import AuditService
from app.services.backup_service import BackupService
from app.services.dto import AuditEntryCreateDTO, BackupCreateDTO


class TestAuditService:
    def test_record_audit_entry(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyAuditRepository(in_memory_session)
        service = AuditService(audit_repo=repo)

        dto = AuditEntryCreateDTO(
            user_id=uuid4(),
            action="CREATE_LETTER",
            entity_type="Letter",
            entity_id=str(uuid4()),
        )
        response = service.record(dto)

        assert response.id is not None
        assert response.action == "CREATE_LETTER"
        assert response.result == "success"

    def test_find_by_user(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyAuditRepository(in_memory_session)
        service = AuditService(audit_repo=repo)

        user_id = uuid4()
        for i in range(3):
            service.record(
                AuditEntryCreateDTO(
                    user_id=user_id,
                    action=f"ACTION_{i}",
                    entity_type="Letter",
                    entity_id=str(uuid4()),
                )
            )

        results = service.find_by_user(user_id)
        assert len(results) == 3

    def test_count_all(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyAuditRepository(in_memory_session)
        service = AuditService(audit_repo=repo)

        for i in range(5):
            service.record(
                AuditEntryCreateDTO(
                    user_id=uuid4(),
                    action=f"A{i}",
                    entity_type="T",
                    entity_id="1",
                )
            )

        assert service.count_all() == 5

    def test_find_by_entity(self, in_memory_session: Session) -> None:
        repo = SQLAlchemyAuditRepository(in_memory_session)
        service = AuditService(audit_repo=repo)

        entity_id = str(uuid4())
        service.record(
            AuditEntryCreateDTO(
                user_id=uuid4(),
                action="VIEW",
                entity_type="Letter",
                entity_id=entity_id,
            )
        )
        results = service.find_by_entity("Letter", entity_id)
        assert len(results) == 1


class TestBackupService:
    def test_create_backup(self, in_memory_session: Session, tmp_path: Path) -> None:
        backup_repo = SQLAlchemyBackupRepository(in_memory_session)

        db_path = tmp_path / "source.db"
        db_mgr = DatabaseManager(db_path)
        db_mgr.initialize()
        Base.metadata.create_all(db_mgr.engine)

        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()

        service = BackupService(
            backup_repo=backup_repo,
            db_manager=db_mgr,
            backup_dir=backup_dir,
        )

        backup_path = backup_dir / "test_backup.db"
        dto = BackupCreateDTO(
            backup_path=str(backup_path),
            size_bytes=0,
            hash_sha256="",
            type=BackupType.MANUAL,
        )
        response = service.create_backup(dto)

        assert response.id is not None
        assert backup_path.exists()
        assert response.hash_sha256 != ""
        assert response.size_bytes > 0

        db_mgr.dispose()

    def test_find_latest(self, in_memory_session: Session, tmp_path: Path) -> None:
        backup_repo = SQLAlchemyBackupRepository(in_memory_session)

        db_path = tmp_path / "source.db"
        db_mgr = DatabaseManager(db_path)
        db_mgr.initialize()
        Base.metadata.create_all(db_mgr.engine)

        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()

        service = BackupService(
            backup_repo=backup_repo,
            db_manager=db_mgr,
            backup_dir=backup_dir,
        )

        dto = BackupCreateDTO(
            backup_path=str(backup_dir / "b1.db"),
            size_bytes=0,
            hash_sha256="",
        )
        service.create_backup(dto)

        latest = service.find_latest()
        assert latest is not None

        db_mgr.dispose()

    def test_verify_backup_integrity_ok(self, in_memory_session: Session, tmp_path: Path) -> None:
        backup_repo = SQLAlchemyBackupRepository(in_memory_session)

        db_path = tmp_path / "source.db"
        db_mgr = DatabaseManager(db_path)
        db_mgr.initialize()
        Base.metadata.create_all(db_mgr.engine)

        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()

        service = BackupService(
            backup_repo=backup_repo,
            db_manager=db_mgr,
            backup_dir=backup_dir,
        )

        dto = BackupCreateDTO(
            backup_path=str(backup_dir / "verify.db"),
            size_bytes=0,
            hash_sha256="",
        )
        response = service.create_backup(dto)
        assert service.verify_backup_integrity(response.id)

        db_mgr.dispose()
