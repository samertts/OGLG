from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ConflictType(Enum):
    VERSION_DIVERGENCE = "version_divergence"
    CONCURRENT_UPDATE = "concurrent_update"
    DELETE_CONFLICT = "delete_conflict"
    CREATE_DUPLICATE = "create_duplicate"
    SCHEMA_MISMATCH = "schema_mismatch"


class MergePolicy(Enum):
    LAST_WRITE_WINS = "last_write_wins"
    SOURCE_PRIORITY = "source_priority"
    TARGET_PRIORITY = "target_priority"
    MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True)
class EntityVersion:
    aggregate_id: str
    version: int
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    node_id: str = ""
    checksum: str = ""


@dataclass(frozen=True)
class SyncConflict:
    conflict_id: str
    conflict_type: ConflictType
    aggregate_id: str
    local_version: EntityVersion
    remote_version: EntityVersion
    data_local: dict[str, Any] = field(default_factory=dict)
    data_remote: dict[str, Any] = field(default_factory=dict)
    policy: MergePolicy = MergePolicy.LAST_WRITE_WINS
    resolved: bool = False


@dataclass(frozen=True)
class ConflictResolution:
    conflict_id: str
    aggregate_id: str
    resolution: dict[str, Any]
    policy_used: MergePolicy
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    resolved_by: str = ""
