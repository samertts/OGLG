from __future__ import annotations

import sqlite3
from typing import Any

from loguru import logger


class FTS5SearchIndex:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None
        self._ensure_fts5()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn

    def _ensure_fts5(self) -> None:
        conn = self._get_conn()
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS letters_fts USING fts5(
                letter_id,
                subject,
                body,
                number,
                sender_name,
                department_name,
                content='',
                tokenize='unicode61'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS letters_fts_metadata (
                letter_id TEXT PRIMARY KEY,
                status TEXT,
                letter_type TEXT,
                priority TEXT,
                classification TEXT,
                department_id TEXT,
                sender_id TEXT,
                created_at TEXT,
                language TEXT
            )
            """
        )
        conn.commit()

    def index_letter(self, letter_id: str, subject: str, body: str, number: str, sender: str, department: str, language: str) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM letters_fts WHERE letter_id = ?", (letter_id,))
        conn.execute(
            "INSERT INTO letters_fts (letter_id, subject, body, number, sender_name, department_name) VALUES (?, ?, ?, ?, ?, ?)",
            (letter_id, subject, body, number, sender, department),
        )
        conn.commit()

    def remove_letter(self, letter_id: str) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM letters_fts WHERE letter_id = ?", (letter_id,))
        conn.execute("DELETE FROM letters_fts_metadata WHERE letter_id = ?", (letter_id,))
        conn.commit()

    def update_metadata(self, letter_id: str, metadata: dict[str, Any]) -> None:
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO letters_fts_metadata
               (letter_id, status, letter_type, priority, classification, department_id, sender_id, created_at, language)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                letter_id,
                metadata.get("status", ""),
                metadata.get("letter_type", ""),
                metadata.get("priority", ""),
                metadata.get("classification", ""),
                metadata.get("department_id", ""),
                metadata.get("sender_id", ""),
                metadata.get("created_at", ""),
                metadata.get("language", ""),
            ),
        )
        conn.commit()

    def search(self, query: str, offset: int = 0, limit: int = 50) -> list[dict[str, Any]]:
        conn = self._get_conn()
        safe_query = self._sanitize_query(query)
        try:
            cursor = conn.execute(
                """SELECT letter_id, subject, body, number, sender_name, department_name, rank
                   FROM letters_fts
                   WHERE letters_fts MATCH ?
                   ORDER BY rank
                   LIMIT ? OFFSET ?""",
                (safe_query, limit, offset),
            )
            results = []
            for row in cursor.fetchall():
                results.append({
                    "letter_id": row[0],
                    "subject": row[1],
                    "body": row[2][:200] if row[2] else "",
                    "number": row[3],
                    "sender_name": row[4],
                    "department_name": row[5],
                    "rank": row[6],
                })
            return results
        except sqlite3.OperationalError as exc:
            logger.warning(f"FTS5 search error: {exc}")
            return []

    def search_advanced(self, filters: dict[str, Any], offset: int = 0, limit: int = 50) -> list[dict[str, Any]]:
        conn = self._get_conn()
        query = filters.get("query", "")
        conditions = []
        params: list[Any] = []

        if query:
            safe_query = self._sanitize_query(query)
            conditions.append("l.letter_id IN (SELECT letter_id FROM letters_fts WHERE letters_fts MATCH ?)")
            params.append(safe_query)

        if filters.get("status"):
            conditions.append("m.status = ?")
            params.append(filters["status"])
        if filters.get("letter_type"):
            conditions.append("m.letter_type = ?")
            params.append(filters["letter_type"])
        if filters.get("priority"):
            conditions.append("m.priority = ?")
            params.append(filters["priority"])
        if filters.get("classification"):
            conditions.append("m.classification = ?")
            params.append(filters["classification"])
        if filters.get("department_id"):
            conditions.append("m.department_id = ?")
            params.append(filters["department_id"])
        if filters.get("sender_id"):
            conditions.append("m.sender_id = ?")
            params.append(filters["sender_id"])
        if filters.get("date_from"):
            conditions.append("m.created_at >= ?")
            params.append(filters["date_from"])
        if filters.get("date_to"):
            conditions.append("m.created_at <= ?")
            params.append(filters["date_to"])

        if not conditions:
            return []

        where_clause = " AND ".join(conditions)
        sql = f"""SELECT l.letter_id, l.subject, l.body, l.number, l.sender_name, l.department_name
                  FROM letters_fts l
                  JOIN letters_fts_metadata m ON l.letter_id = m.letter_id
                  WHERE {where_clause}
                  LIMIT ? OFFSET ?"""
        params.extend([limit, offset])

        try:
            cursor = conn.execute(sql, params)
            results = []
            for row in cursor.fetchall():
                results.append({
                    "letter_id": row[0],
                    "subject": row[1],
                    "body": row[2][:200] if row[2] else "",
                    "number": row[3],
                    "sender_name": row[4],
                    "department_name": row[5],
                })
            return results
        except sqlite3.OperationalError as exc:
            logger.warning(f"FTS5 advanced search error: {exc}")
            return []

    def count(self, query: str) -> int:
        conn = self._get_conn()
        safe_query = self._sanitize_query(query)
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM letters_fts WHERE letters_fts MATCH ?",
                (safe_query,),
            )
            return cursor.fetchone()[0] or 0
        except sqlite3.OperationalError:
            return 0

    def count_advanced(self, filters: dict[str, Any]) -> int:
        conn = self._get_conn()
        query = filters.get("query", "")
        conditions = []
        params: list[Any] = []

        if query:
            safe_query = self._sanitize_query(query)
            conditions.append("l.letter_id IN (SELECT letter_id FROM letters_fts WHERE letters_fts MATCH ?)")
            params.append(safe_query)

        if filters.get("status"):
            conditions.append("m.status = ?")
            params.append(filters["status"])
        if filters.get("letter_type"):
            conditions.append("m.letter_type = ?")
            params.append(filters["letter_type"])
        if filters.get("priority"):
            conditions.append("m.priority = ?")
            params.append(filters["priority"])
        if filters.get("classification"):
            conditions.append("m.classification = ?")
            params.append(filters["classification"])
        if filters.get("department_id"):
            conditions.append("m.department_id = ?")
            params.append(filters["department_id"])
        if filters.get("sender_id"):
            conditions.append("m.sender_id = ?")
            params.append(filters["sender_id"])
        if filters.get("date_from"):
            conditions.append("m.created_at >= ?")
            params.append(filters["date_from"])
        if filters.get("date_to"):
            conditions.append("m.created_at <= ?")
            params.append(filters["date_to"])

        if not conditions:
            return 0

        where_clause = " AND ".join(conditions)
        sql = f"""SELECT COUNT(*)
                  FROM letters_fts l
                  JOIN letters_fts_metadata m ON l.letter_id = m.letter_id
                  WHERE {where_clause}"""

        try:
            cursor = conn.execute(sql, params)
            return cursor.fetchone()[0] or 0
        except sqlite3.OperationalError:
            return 0

    def _sanitize_query(self, query: str) -> str:
        import re
        sanitized = re.sub(r'[^\w\s\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\-]', ' ', query)
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        terms = sanitized.split()
        if not terms:
            return "*"
        return " AND ".join(f'"{t}"' if " " in t else t for t in terms[:10])

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
