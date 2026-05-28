from __future__ import annotations

from enum import Enum


class ArchiveState(Enum):
    ACTIVE = "ACTIVE"
    SOFT_DELETED = "SOFT_DELETED"
    ARCHIVED = "ARCHIVED"
    PENDING_PURGE = "PENDING_PURGE"
    PURGED = "PURGED"

    @property
    def is_recoverable(self) -> bool:
        return self in (ArchiveState.ACTIVE, ArchiveState.SOFT_DELETED, ArchiveState.ARCHIVED)

    @property
    def is_accessible(self) -> bool:
        return self in (ArchiveState.ACTIVE, ArchiveState.ARCHIVED)
