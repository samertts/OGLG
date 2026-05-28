from __future__ import annotations

from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from app.core.entities.audit_entry import AuditEntry


class AuditRepository(Protocol):
    """Append-only repository for audit entries."""

    @abstractmethod
    def append(self, entry: AuditEntry) -> AuditEntry: ...

    @abstractmethod
    def find_by_id(self, id: UUID) -> AuditEntry | None: ...

    @abstractmethod
    def find_by_user(self, user_id: UUID, offset: int = 0, limit: int = 50) -> list[AuditEntry]: ...

    @abstractmethod
    def find_by_entity(
        self, entity_type: str, entity_id: str, offset: int = 0, limit: int = 50
    ) -> list[AuditEntry]: ...

    @abstractmethod
    def find_by_action(self, action: str, offset: int = 0, limit: int = 50) -> list[AuditEntry]: ...

    @abstractmethod
    def find_by_date_range(
        self, start: str | None, end: str | None, offset: int = 0, limit: int = 50
    ) -> list[AuditEntry]: ...

    @abstractmethod
    def count_all(self) -> int: ...
