from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.events.base import DomainEvent, EventMetadata
from app.core.safety.crash import CrashSafeWrapper


class EventStore:
    """Append-only SQLite event storage with WAL-safe persistence."""

    def __init__(
        self,
        db_path: str | Path,
        max_replay_window: int = 10000,
    ) -> None:
        self._path = Path(db_path)
        self._max_window = max_replay_window
        self._lock = threading.RLock()
        self._crash_safe = CrashSafeWrapper(reraise=True)
        self._conn: sqlite3.Connection | None = None
        self._seq = 0

    def open(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self._path),
            timeout=5.0,
        )
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA synchronous = NORMAL")
        self._conn.execute("PRAGMA busy_timeout = 5000")
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        self._seq = self._read_max_sequence()

    def _init_schema(self) -> None:
        if self._conn is None:
            raise RuntimeError("Store not open")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS event_store (
                sequence   INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id   TEXT NOT NULL UNIQUE,
                event_type TEXT NOT NULL,
                aggregate_id TEXT NOT NULL,
                data       TEXT NOT NULL,
                metadata   TEXT NOT NULL,
                version    INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_event_store_type
                ON event_store(event_type);
            CREATE INDEX IF NOT EXISTS idx_event_store_aggregate
                ON event_store(aggregate_id);
            CREATE INDEX IF NOT EXISTS idx_event_store_sequence
                ON event_store(sequence);
            CREATE TABLE IF NOT EXISTS replay_checkpoint (
                checkpoint_id TEXT PRIMARY KEY,
                last_sequence INTEGER NOT NULL,
                created_at    TEXT NOT NULL
            );
        """)
        self._conn.commit()

    def _read_max_sequence(self) -> int:
        if self._conn is None:
            return 0
        row = self._conn.execute(
            "SELECT COALESCE(MAX(sequence), 0) as seq FROM event_store"
        ).fetchone()
        return row["seq"] if row else 0

    def append(
        self,
        event: DomainEvent,
    ) -> int:
        with self._lock:
            if self._conn is None:
                raise RuntimeError("Store not open")
            self._seq += 1
            seq = self._seq
            meta_dict = {
                "id": event.event_id,
                "correlation_id": event.correlation_id,
                "causation_id": event.causation_id,
                "timestamp": event.timestamp.isoformat(),
                "sequence": seq,
                "replay": event.is_replay,
                "source": event.metadata.source,
            }
            self._conn.execute(
                """INSERT OR FAIL INTO event_store
                   (sequence, event_id, event_type, aggregate_id,
                    data, metadata, version, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    seq,
                    event.event_id,
                    event.event_type,
                    event.aggregate_id,
                    json.dumps(event.data, sort_keys=True),
                    json.dumps(meta_dict, sort_keys=True),
                    event.version,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            self._conn.commit()
            return seq

    def read_since(
        self,
        sequence: int = 0,
        limit: int = 1000,
    ) -> list[DomainEvent]:
        with self._lock:
            if self._conn is None:
                raise RuntimeError("Store not open")
            limit = min(limit, self._max_window)
            rows = self._conn.execute(
                """SELECT * FROM event_store
                   WHERE sequence > ?
                   ORDER BY sequence ASC
                   LIMIT ?""",
                (sequence, limit),
            ).fetchall()
            return [self._row_to_event(r) for r in rows]

    def read_by_type(
        self,
        event_type: str,
        sequence: int = 0,
        limit: int = 1000,
    ) -> list[DomainEvent]:
        with self._lock:
            if self._conn is None:
                raise RuntimeError("Store not open")
            limit = min(limit, self._max_window)
            rows = self._conn.execute(
                """SELECT * FROM event_store
                   WHERE event_type = ? AND sequence > ?
                   ORDER BY sequence ASC
                   LIMIT ?""",
                (event_type, sequence, limit),
            ).fetchall()
            return [self._row_to_event(r) for r in rows]

    def read_by_aggregate(
        self,
        aggregate_id: str,
        sequence: int = 0,
        limit: int = 1000,
    ) -> list[DomainEvent]:
        with self._lock:
            if self._conn is None:
                raise RuntimeError("Store not open")
            limit = min(limit, self._max_window)
            rows = self._conn.execute(
                """SELECT * FROM event_store
                   WHERE aggregate_id = ? AND sequence > ?
                   ORDER BY sequence ASC
                   LIMIT ?""",
                (aggregate_id, sequence, limit),
            ).fetchall()
            return [self._row_to_event(r) for r in rows]

    def save_checkpoint(
        self,
        checkpoint_id: str = "default",
    ) -> str:
        with self._lock:
            if self._conn is None:
                raise RuntimeError("Store not open")
            now = datetime.now(timezone.utc).isoformat()
            self._conn.execute(
                """INSERT OR REPLACE INTO replay_checkpoint
                   (checkpoint_id, last_sequence, created_at)
                   VALUES (?, ?, ?)""",
                (checkpoint_id, self._seq, now),
            )
            self._conn.commit()
            return checkpoint_id

    def load_checkpoint(
        self,
        checkpoint_id: str = "default",
    ) -> int:
        if self._conn is None:
            raise RuntimeError("Store not open")
        row = self._conn.execute(
            "SELECT last_sequence FROM replay_checkpoint WHERE checkpoint_id = ?",
            (checkpoint_id,),
        ).fetchone()
        return row["last_sequence"] if row else 0

    @property
    def max_sequence(self) -> int:
        return self._seq

    @property
    def event_count(self) -> int:
        if self._conn is None:
            return 0
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM event_store"
        ).fetchone()
        return row["cnt"] if row else 0

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def _row_to_event(self, row: sqlite3.Row) -> DomainEvent:
        data = json.loads(row["data"])
        meta_dict = json.loads(row["metadata"])
        meta = EventMetadata(
            id=meta_dict.get("id", row["event_id"]),
            correlation_id=meta_dict.get("correlation_id", ""),
            causation_id=meta_dict.get("causation_id", ""),
            timestamp=datetime.fromisoformat(
                meta_dict.get("timestamp", row["created_at"])
            ),
            sequence=row["sequence"],
            replay=meta_dict.get("replay", False),
            source=meta_dict.get("source", ""),
        )
        return DomainEvent(
            aggregate_id=row["aggregate_id"],
            event_type=row["event_type"],
            data=data,
            metadata=meta,
            version=row["version"],
        )

    def state(self) -> dict[str, Any]:
        with self._lock:
            return {
                "path": str(self._path),
                "max_sequence": self._seq,
                "event_count": self.event_count,
                "max_replay_window": self._max_window,
                "open": self._conn is not None,
            }
