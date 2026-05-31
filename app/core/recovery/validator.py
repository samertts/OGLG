from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.core.diagnostics.wal_check import WalConsistencyChecker


class WalRecoveryValidator:
    """WAL recovery validation with crash recovery assessment."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._wal_path = self._db_path.with_name(
            self._db_path.name + "-wal"
        )

    def validate(self) -> dict[str, Any]:
        db_ok = self._check_db_integrity()
        wal_result = self._check_wal()
        return {
            "database_ok": db_ok["valid"],
            "wal_ok": wal_result["valid"],
            "recovery_needed": not db_ok["valid"] or not wal_result["valid"],
            "database": db_ok,
            "wal": wal_result,
            "message": self._build_message(db_ok, wal_result),
        }

    def _check_db_integrity(self) -> dict[str, Any]:
        if not self._db_path.exists():
            return {
                "valid": False,
                "message": "Database file not found",
            }
        try:
            conn = sqlite3.connect(str(self._db_path), timeout=5.0)
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            if row and row[0] == "ok":
                return {"valid": True, "message": "Integrity check passed"}
            return {
                "valid": False,
                "message": f"Integrity check failed: {row[0] if row else 'unknown'}",
            }
        except sqlite3.Error as exc:
            return {"valid": False, "message": f"Database error: {exc}"}

    def _check_wal(self) -> dict[str, Any]:
        checker = WalConsistencyChecker(self._wal_path)
        return checker.check()

    @staticmethod
    def _build_message(
        db: dict[str, Any], wal: dict[str, Any]
    ) -> str:
        if db["valid"] and wal.get("valid", True):
            return "All checks passed — system healthy"
        if not db["valid"]:
            return f"Database needs recovery: {db['message']}"
        if not wal.get("valid", True):
            return f"WAL needs recovery: {wal['message']}"
        return "Recovery recommended"
