from __future__ import annotations

from typing import Any

from app.core.archive.indexer import ArchiveIndexer


class ArchiveIntegrityValidator:
    """Corruption detection for archived snapshots."""

    def __init__(self, indexer: ArchiveIndexer) -> None:
        self._indexer = indexer

    def validate(self, snapshot_id: str) -> dict[str, Any]:
        valid = self._indexer.verify_integrity(snapshot_id)
        return {
            "snapshot_id": snapshot_id,
            "valid": valid,
            "corrupted": not valid,
            "message": "Checksum matches" if valid else "Checksum mismatch — data may be corrupted",
        }

    def validate_all(self, limit: int = 1000) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        conn = getattr(self._indexer, "_conn", None)
        if conn is None:
            return results
        rows = conn.execute(
            "SELECT snapshot_id FROM archive_index LIMIT ?",
            (limit,),
        ).fetchall()
        for row in rows:
            results.append(self.validate(row["snapshot_id"]))
        return results
