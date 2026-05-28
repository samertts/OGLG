"""Backup service — create, query, and manage database backups."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from app.core.entities.backup_log import BackupLog
from app.core.enums import BackupType
from app.core.repositories.backup_repository import BackupRepository
from app.database.connection import DatabaseManager
from app.services.dto import BackupCreateDTO, BackupResponseDTO
from app.utils.file_utils import compute_file_hash
from app.utils.logger import get_logger

logger = get_logger("app.services.backup_service")


@dataclass
class BackupService:
    backup_repo: BackupRepository
    db_manager: DatabaseManager
    backup_dir: Path

    def create_backup(
        self,
        dto: BackupCreateDTO,
    ) -> BackupResponseDTO:
        backup_path = Path(dto.backup_path)
        self.db_manager.backup_to(backup_path)

        size_bytes = backup_path.stat().st_size
        hash_sha256 = compute_file_hash(backup_path)

        entity = BackupLog(
            id=uuid4(),
            backup_path=str(backup_path.resolve()),
            size_bytes=size_bytes,
            hash_sha256=hash_sha256,
            type=dto.type,
            created_by_id=dto.created_by_id,
            created_at=datetime.now(),
            notes=dto.notes,
        )
        saved = self.backup_repo.append(entity)
        logger.info(
            "Backup created",
            extra={
                "path": str(backup_path),
                "size": size_bytes,
                "hash": hash_sha256[:16],
                "type": dto.type.value,
            },
        )
        return BackupResponseDTO.from_entity(saved)

    def create_auto_backup(self) -> BackupResponseDTO | None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"auto_backup_{timestamp}.db"
        dto = BackupCreateDTO(
            backup_path=str(backup_path),
            size_bytes=0,
            hash_sha256="",
            type=BackupType.AUTO,
            notes="Automatic periodic backup",
        )
        return self.create_backup(dto)

    def find_by_id(self, backup_id: UUID) -> BackupResponseDTO | None:
        found = self.backup_repo.find_by_id(backup_id)
        return BackupResponseDTO.from_entity(found) if found else None

    def find_all(self, offset: int = 0, limit: int = 50) -> list[BackupResponseDTO]:
        return [
            BackupResponseDTO.from_entity(e)
            for e in self.backup_repo.find_all(offset, limit)
        ]

    def find_by_type(self, type: BackupType) -> list[BackupResponseDTO]:
        return [
            BackupResponseDTO.from_entity(e)
            for e in self.backup_repo.find_by_type(type)
        ]

    def find_latest(self) -> BackupResponseDTO | None:
        found = self.backup_repo.find_latest()
        return BackupResponseDTO.from_entity(found) if found else None

    def mark_restored(self, backup_id: UUID, user_id: UUID) -> None:
        self.backup_repo.mark_restored(backup_id, user_id)
        logger.info(
            "Backup marked as restored",
            extra={"backup_id": str(backup_id), "user_id": str(user_id)},
        )

    def verify_backup_integrity(self, backup_id: UUID) -> bool:
        entry = self.backup_repo.find_by_id(backup_id)
        if not entry:
            return False
        path = Path(entry.backup_path)
        if not path.exists():
            return False
        actual_hash = compute_file_hash(path)
        return actual_hash == entry.hash_sha256
