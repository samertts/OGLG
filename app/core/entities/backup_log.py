from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.core.enums import BackupType


@dataclass
class BackupLog:
    id: UUID = field(default_factory=uuid4)
    backup_path: str = ""
    size_bytes: int = 0
    hash_sha256: str = ""
    type: BackupType = BackupType.MANUAL
    created_by_id: UUID | None = None
    created_at: datetime = field(default_factory=datetime.now)
    restored_at: datetime | None = None
    restored_by_id: UUID | None = None
    notes: str | None = None
