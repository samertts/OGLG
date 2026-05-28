"""Audit service — append-only audit trail for all domain operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.core.entities.audit_entry import AuditEntry
from app.core.repositories.audit_repository import AuditRepository
from app.services.dto import AuditEntryCreateDTO, AuditEntryResponseDTO


@dataclass
class AuditService:
    audit_repo: AuditRepository

    def record(
        self,
        dto: AuditEntryCreateDTO,
    ) -> AuditEntryResponseDTO:
        entity = AuditEntry(
            id=uuid4(),
            timestamp=datetime.now(),
            user_id=dto.user_id,
            action=dto.action,
            entity_type=dto.entity_type,
            entity_id=dto.entity_id,
            details_json=dto.details_json,
            ip_address=dto.ip_address,
            result=dto.result,
        )
        saved = self.audit_repo.append(entity)
        return AuditEntryResponseDTO.from_entity(saved)

    def find_by_id(self, entry_id: UUID) -> AuditEntryResponseDTO | None:
        found = self.audit_repo.find_by_id(entry_id)
        return AuditEntryResponseDTO.from_entity(found) if found else None

    def find_by_user(
        self, user_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[AuditEntryResponseDTO]:
        return [
            AuditEntryResponseDTO.from_entity(e)
            for e in self.audit_repo.find_by_user(user_id, offset, limit)
        ]

    def find_by_entity(
        self, entity_type: str, entity_id: str, offset: int = 0, limit: int = 50
    ) -> list[AuditEntryResponseDTO]:
        return [
            AuditEntryResponseDTO.from_entity(e)
            for e in self.audit_repo.find_by_entity(entity_type, entity_id, offset, limit)
        ]

    def find_by_action(
        self, action: str, offset: int = 0, limit: int = 50
    ) -> list[AuditEntryResponseDTO]:
        return [
            AuditEntryResponseDTO.from_entity(e)
            for e in self.audit_repo.find_by_action(action, offset, limit)
        ]

    def find_by_date_range(
        self, start: str | None = None, end: str | None = None, offset: int = 0, limit: int = 50
    ) -> list[AuditEntryResponseDTO]:
        return [
            AuditEntryResponseDTO.from_entity(e)
            for e in self.audit_repo.find_by_date_range(start, end, offset, limit)
        ]

    def count_all(self) -> int:
        return self.audit_repo.count_all()
