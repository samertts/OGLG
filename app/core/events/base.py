from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


EventId = str


@dataclass(frozen=True)
class EventMetadata:
    id: EventId = field(default_factory=lambda: uuid.uuid4().hex)
    correlation_id: str = ""
    causation_id: str = ""
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    sequence: int = 0
    replay: bool = False
    source: str = ""


@dataclass(frozen=True)
class DomainEvent:
    aggregate_id: str
    event_type: str
    data: dict[str, Any]
    metadata: EventMetadata = field(default_factory=EventMetadata)
    version: int = 1

    @property
    def event_id(self) -> EventId:
        return self.metadata.id

    @property
    def correlation_id(self) -> str:
        return self.metadata.correlation_id

    @property
    def causation_id(self) -> str:
        return self.metadata.causation_id

    @property
    def timestamp(self) -> datetime:
        return self.metadata.timestamp

    @property
    def is_replay(self) -> bool:
        return self.metadata.replay

    def with_metadata(
        self,
        correlation_id: str = "",
        causation_id: str = "",
        source: str = "",
    ) -> DomainEvent:
        meta = EventMetadata(
            id=self.metadata.id,
            correlation_id=correlation_id or self.metadata.correlation_id,
            causation_id=causation_id or self.metadata.causation_id,
            timestamp=self.metadata.timestamp,
            sequence=self.metadata.sequence,
            replay=self.metadata.replay,
            source=source or self.metadata.source,
        )
        return DomainEvent(
            aggregate_id=self.aggregate_id,
            event_type=self.event_type,
            data=self.data,
            metadata=meta,
            version=self.version,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "data": self.data,
            "version": self.version,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "timestamp": self.timestamp.isoformat(),
            "sequence": self.metadata.sequence,
            "replay": self.is_replay,
            "source": self.metadata.source,
        }
