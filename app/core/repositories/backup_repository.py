from __future__ import annotations

from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from app.core.entities.backup_log import BackupLog
from app.core.enums import BackupType


class BackupRepository(Protocol):
    """Append-only repository for backup logs."""

    @abstractmethod
    def append(self, entry: BackupLog) -> BackupLog:
        ...

    @abstractmethod
    def find_by_id(self, id: UUID) -> BackupLog | None:
        ...

    @abstractmethod
    def find_all(self, offset: int = 0, limit: int = 50) -> list[BackupLog]:
        ...

    @abstractmethod
    def find_by_type(self, type: BackupType) -> list[BackupLog]:
        ...

    @abstractmethod
    def find_latest(self) -> BackupLog | None:
        ...

    @abstractmethod
    def mark_restored(self, id: UUID, user_id: UUID) -> None:
        ...
