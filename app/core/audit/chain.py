from __future__ import annotations

import hashlib
import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class AuditEntry:
    entry_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    sequence: int = 0
    event_type: str = ""
    aggregate_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    previous_hash: str = ""
    hash: str = ""
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    source: str = ""

    def compute_hash(self) -> str:
        raw = json.dumps(
            {
                "entry_id": self.entry_id,
                "sequence": self.sequence,
                "event_type": self.event_type,
                "aggregate_id": self.aggregate_id,
                "data": self.data,
                "previous_hash": self.previous_hash,
                "timestamp": self.timestamp.isoformat(),
            },
            sort_keys=True,
        )
        return hashlib.sha256(raw.encode()).hexdigest()


@dataclass(frozen=True)
class AuditSnapshot:
    sequence: int
    root_hash: str
    tip_hash: str
    entry_count: int
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class AuditChain:
    """Append-only audit event chain with chained hashes."""

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []
        self._lock = threading.RLock()
        self._sequence = 0

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    @property
    def tip_hash(self) -> str:
        with self._lock:
            if not self._entries:
                return ""
            return self._entries[-1].hash

    @property
    def root_hash(self) -> str:
        with self._lock:
            if not self._entries:
                return ""
            return self._entries[0].hash

    def append(
        self,
        event_type: str,
        aggregate_id: str = "",
        data: dict[str, Any] | None = None,
        source: str = "",
    ) -> AuditEntry:
        with self._lock:
            self._sequence += 1
            previous_hash = self.tip_hash
            entry = AuditEntry(
                entry_id=uuid.uuid4().hex,
                sequence=self._sequence,
                event_type=event_type,
                aggregate_id=aggregate_id,
                data=data or {},
                previous_hash=previous_hash,
                timestamp=datetime.now(timezone.utc),
                source=source,
            )
            computed = entry.compute_hash()
            object.__setattr__(entry, "hash", computed)
            self._entries.append(entry)
            return entry

    def verify_chain(self) -> bool:
        with self._lock:
            for i, entry in enumerate(self._entries):
                if entry.hash != entry.compute_hash():
                    return False
                if i > 0:
                    if entry.previous_hash != self._entries[i - 1].hash:
                        return False
            return True

    def get_entry(self, sequence: int) -> AuditEntry | None:
        with self._lock:
            for entry in self._entries:
                if entry.sequence == sequence:
                    return entry
            return None

    def get_entries_since(self, sequence: int) -> list[AuditEntry]:
        with self._lock:
            return [e for e in self._entries if e.sequence > sequence]

    def snapshot(self) -> AuditSnapshot:
        with self._lock:
            return AuditSnapshot(
                sequence=self._sequence,
                root_hash=self.root_hash,
                tip_hash=self.tip_hash,
                entry_count=self.entry_count,
            )

    def state(self) -> dict[str, Any]:
        with self._lock:
            return {
                "entry_count": self.entry_count,
                "sequence": self._sequence,
                "root_hash": self.root_hash,
                "tip_hash": self.tip_hash,
                "chain_valid": self.verify_chain(),
            }
