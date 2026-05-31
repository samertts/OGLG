from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.archive.snapshot import ArchiveSnapshot


class ArchiveIndexer:
    """Immutable archive indexer with SHA-256 integrity and bounded memory."""

    def __init__(
        self,
        db_path: str | Path,
        batch_size: int = 100,
    ) -> None:
        self._path = Path(db_path)
        self._batch_size = batch_size
        self._lock = threading.RLock()
        self._conn: sqlite3.Connection | None = None

    def open(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path), timeout=5.0)
        self._conn.execute("PRAGMA journal_mode = WAL")
        self._conn.execute("PRAGMA synchronous = NORMAL")
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        if self._conn is None:
            raise RuntimeError("Indexer not open")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS archive_index (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id TEXT NOT NULL UNIQUE,
                archive_type TEXT NOT NULL,
                source_id   TEXT NOT NULL,
                checksum    TEXT NOT NULL,
                data        TEXT NOT NULL,
                metadata    TEXT NOT NULL DEFAULT '{}',
                created_at  TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_archive_type
                ON archive_index(archive_type);
            CREATE INDEX IF NOT EXISTS idx_archive_source
                ON archive_index(source_id);
            CREATE INDEX IF NOT EXISTS idx_archive_checksum
                ON archive_index(checksum);
            CREATE TABLE IF NOT EXISTS archive_attachment (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id TEXT NOT NULL,
                file_name   TEXT NOT NULL,
                file_hash   TEXT NOT NULL,
                file_size   INTEGER NOT NULL DEFAULT 0,
                metadata    TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY (snapshot_id) REFERENCES archive_index(snapshot_id)
            );
        """)
        self._conn.commit()

    def index(self, snapshot: ArchiveSnapshot) -> str:
        with self._lock:
            if self._conn is None:
                raise RuntimeError("Indexer not open")
            validated = (
                snapshot.with_checksum()
                if not snapshot.checksum
                else snapshot
            )
            self._conn.execute(
                """INSERT OR FAIL INTO archive_index
                   (snapshot_id, archive_type, source_id,
                    checksum, data, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    validated.snapshot_id,
                    validated.archive_type,
                    validated.source_id,
                    validated.checksum,
                    json.dumps(validated.data, sort_keys=True),
                    json.dumps(validated.metadata, sort_keys=True),
                    validated.created_at.isoformat(),
                ),
            )
            self._conn.commit()
            return validated.snapshot_id

    def link_attachment(
        self,
        snapshot_id: str,
        file_name: str,
        file_hash: str,
        file_size: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self._lock:
            if self._conn is None:
                raise RuntimeError("Indexer not open")
            self._conn.execute(
                """INSERT INTO archive_attachment
                   (snapshot_id, file_name, file_hash, file_size, metadata)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    snapshot_id,
                    file_name,
                    file_hash,
                    file_size,
                    json.dumps(metadata or {}, sort_keys=True),
                ),
            )
            self._conn.commit()

    def verify_integrity(self, snapshot_id: str) -> bool:
        if self._conn is None:
            raise RuntimeError("Indexer not open")
        row = self._conn.execute(
            "SELECT * FROM archive_index WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()
        if row is None:
            return False
        data = json.loads(row["data"])
        meta = json.loads(row["metadata"])
        snap = ArchiveSnapshot(
            snapshot_id=row["snapshot_id"],
            archive_type=row["archive_type"],
            source_id=row["source_id"],
            data=data,
            metadata=meta,
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        return snap.compute_checksum() == row["checksum"]

    def lookup(self, snapshot_id: str) -> ArchiveSnapshot | None:
        if self._conn is None:
            raise RuntimeError("Indexer not open")
        row = self._conn.execute(
            "SELECT * FROM archive_index WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()
        if row is None:
            return None
        return ArchiveSnapshot(
            snapshot_id=row["snapshot_id"],
            archive_type=row["archive_type"],
            source_id=row["source_id"],
            data=json.loads(row["data"]),
            checksum=row["checksum"],
            metadata=json.loads(row["metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    @property
    def count(self) -> int:
        if self._conn is None:
            return 0
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM archive_index"
        ).fetchone()
        return row["cnt"] if row else 0

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None
