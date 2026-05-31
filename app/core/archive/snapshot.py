from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

SnapshotId = str


@dataclass(frozen=True)
class ArchiveSnapshot:
    snapshot_id: SnapshotId = field(
        default_factory=lambda: uuid.uuid4().hex
    )
    archive_type: str = ""
    source_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    checksum: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def compute_checksum(self) -> str:
        raw = json.dumps(
            {
                "snapshot_id": self.snapshot_id,
                "archive_type": self.archive_type,
                "source_id": self.source_id,
                "data": self.data,
                "metadata": self.metadata,
                "created_at": self.created_at.isoformat(),
            },
            sort_keys=True,
        )
        return hashlib.sha256(raw.encode()).hexdigest()

    def with_checksum(self) -> ArchiveSnapshot:
        ck = self.compute_checksum()
        return ArchiveSnapshot(
            snapshot_id=self.snapshot_id,
            archive_type=self.archive_type,
            source_id=self.source_id,
            data=self.data,
            checksum=ck,
            metadata=self.metadata,
            created_at=self.created_at,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "archive_type": self.archive_type,
            "source_id": self.source_id,
            "data": self.data,
            "checksum": self.checksum,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
