from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.federation.identity import NodeId


@dataclass(frozen=True)
class SyncMetadata:
    sync_id: str
    source_node: NodeId
    target_node: NodeId
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    sequence: int = 0
    checksum: str = ""


@dataclass(frozen=True)
class FederationEvent:
    event_type: str
    source: NodeId
    aggregate_id: str
    data: dict[str, Any]
    metadata: SyncMetadata
    version: int = 1

    @property
    def sync_id(self) -> str:
        return self.metadata.sync_id


@dataclass(frozen=True)
class SyncManifest:
    source_node: NodeId
    target_node: NodeId
    events: list[FederationEvent] = field(default_factory=list)
    checkpoint: str = ""
    checksum: str = ""
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass(frozen=True)
class SyncCheckpoint:
    node_id: NodeId
    sequence: int = 0
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    checksum: str = ""


@dataclass
class SyncSession:
    session_id: str = ""
    source_node: NodeId = ""
    target_node: NodeId = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    events_synced: int = 0
    errors: list[str] = field(default_factory=list)
    checkpoint: SyncCheckpoint | None = None

    def start(self) -> None:
        self.started_at = datetime.now(timezone.utc)

    def complete(self) -> None:
        self.completed_at = datetime.now(timezone.utc)
