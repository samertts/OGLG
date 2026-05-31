from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RowId = int


@dataclass
class SearchQuery:
    text: str = ""
    sender: str = ""
    recipient: str = ""
    subject: str = ""
    date_from: str = ""
    date_to: str = ""
    archive_type: str = ""
    page: int = 0
    page_size: int = 20
    arabic_normalize: bool = True

    @property
    def offset(self) -> int:
        return self.page * self.page_size

    @property
    def bounded_page_size(self) -> int:
        return min(self.page_size, 200)


@dataclass
class SearchResult:
    row_id: RowId
    snapshot_id: str
    archive_type: str
    source_id: str
    snippet: str
    score: float = 0.0
    created_at: str = ""


class SearchEngine:
    """Deterministic search engine with bounded pagination and Arabic support."""

    def __init__(
        self,
        db_path: str | Path,
        max_results: int = 200,
    ) -> None:
        self._path = Path(db_path)
        self._max_results = max_results
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
            raise RuntimeError("Engine not open")
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS search_index (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id TEXT NOT NULL,
                archive_type TEXT NOT NULL,
                source_id   TEXT NOT NULL,
                sender      TEXT NOT NULL DEFAULT '',
                recipient   TEXT NOT NULL DEFAULT '',
                subject     TEXT NOT NULL DEFAULT '',
                body        TEXT NOT NULL DEFAULT '',
                created_at  TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_search_sender
                ON search_index(sender);
            CREATE INDEX IF NOT EXISTS idx_search_recipient
                ON search_index(recipient);
            CREATE INDEX IF NOT EXISTS idx_search_subject
                ON search_index(subject);
            CREATE INDEX IF NOT EXISTS idx_search_type
                ON search_index(archive_type);
        """)

    def index_document(
        self,
        snapshot_id: str,
        archive_type: str,
        source_id: str,
        sender: str = "",
        recipient: str = "",
        subject: str = "",
        body: str = "",
    ) -> int:
        with self._lock:
            if self._conn is None:
                raise RuntimeError("Engine not open")
            now = datetime.now(timezone.utc).isoformat()
            cur = self._conn.execute(
                """INSERT INTO search_index
                   (snapshot_id, archive_type, source_id,
                    sender, recipient, subject, body, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    snapshot_id,
                    archive_type,
                    source_id,
                    self._normalize(sender),
                    self._normalize(recipient),
                    self._normalize(subject),
                    self._normalize(body),
                    now,
                ),
            )
            self._conn.commit()
            return cur.lastrowid or 0

    def search(
        self,
        query: SearchQuery,
    ) -> list[SearchResult]:
        if self._conn is None:
            raise RuntimeError("Engine not open")
        conditions: list[str] = []
        params: list[Any] = []
        q = self._normalize(query.text)

        if q:
            for col in ("sender", "recipient", "subject", "body"):
                conditions.append(f"{col} LIKE ?")
                params.append(f"%{q}%")
        if query.sender:
            conditions.append("sender LIKE ?")
            params.append(f"%{self._normalize(query.sender)}%")
        if query.recipient:
            conditions.append("recipient LIKE ?")
            params.append(f"%{self._normalize(query.recipient)}%")
        if query.subject:
            conditions.append("subject LIKE ?")
            params.append(f"%{self._normalize(query.subject)}%")
        if query.archive_type:
            conditions.append("archive_type = ?")
            params.append(query.archive_type)

        where = " OR ".join(conditions) if conditions else "1=1"
        limit = min(query.bounded_page_size, self._max_results)

        sql = (
            f"SELECT * FROM search_index WHERE {where}"
            f" ORDER BY id DESC LIMIT ? OFFSET ?"
        )
        params.extend([limit, query.offset])

        rows = self._conn.execute(sql, params).fetchall()
        results: list[SearchResult] = []
        for row in rows:
            snippet = self._build_snippet(row, q)
            results.append(
                SearchResult(
                    row_id=row["id"],
                    snapshot_id=row["snapshot_id"],
                    archive_type=row["archive_type"],
                    source_id=row["source_id"],
                    snippet=snippet,
                    score=1.0,
                    created_at=row["created_at"],
                )
            )
        return results

    def _build_snippet(
        self, row: sqlite3.Row, query: str
    ) -> str:
        if query and query in row["body"]:
            idx = row["body"].find(query)
            start = max(0, idx - 40)
            end = min(len(row["body"]), idx + len(query) + 40)
            snippet = row["body"][start:end]
            if start > 0:
                snippet = "..." + snippet
            if end < len(row["body"]):
                snippet = snippet + "..."
            return snippet
        if row["subject"]:
            return row["subject"][:100]
        if row["sender"]:
            return f"From: {row['sender']}"
        return f"{row['archive_type']}:{row['source_id']}"

    @staticmethod
    def _normalize(text: str) -> str:
        normalized = text.lower().strip()
        normalized = (
            normalized.replace("أ", "ا")
            .replace("إ", "ا")
            .replace("آ", "ا")
            .replace("ى", "ي")
            .replace("ة", "ه")
            .replace("ؤ", "و")
            .replace("ئ", "ي")
        )
        return normalized

    @property
    def document_count(self) -> int:
        if self._conn is None:
            return 0
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM search_index"
        ).fetchone()
        return row["cnt"] if row else 0

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def state(self) -> dict[str, Any]:
        return {
            "path": str(self._path),
            "document_count": self.document_count,
            "max_results": self._max_results,
            "open": self._conn is not None,
        }
