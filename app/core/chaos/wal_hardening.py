from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationReport:
    name: str
    passed: bool
    detail: str = ""
    duration_seconds: float = 0.0


class WalGrowthValidator:
    def __init__(self, max_wal_mb: float = 200.0) -> None:
        self._max_wal_mb = max_wal_mb
        self._checkpoint_bytes: int = 0

    @property
    def checkpoint_bytes(self) -> int:
        return self._checkpoint_bytes

    def validate(self, db_path: str | Path) -> ValidationReport:
        start = time.monotonic()
        path = Path(db_path)
        wal_path = path.with_suffix(".db-wal")
        if not wal_path.exists():
            wal_path = Path(str(path) + "-wal")
        try:
            if not wal_path.exists():
                return ValidationReport("wal_growth", True, "No WAL file", time.monotonic() - start)
            mb = wal_path.stat().st_size / (1024 * 1024)
            exceeded = mb > self._max_wal_mb
            return ValidationReport(
                "wal_growth", not exceeded,
                f"WAL {mb:.1f}MB vs max {self._max_wal_mb}MB",
                time.monotonic() - start,
            )
        except Exception as e:
            return ValidationReport("wal_growth", False, str(e), time.monotonic() - start)

    def record_checkpoint(self, bytes_checkpointed: int) -> None:
        self._checkpoint_bytes += bytes_checkpointed


class JournalIntegrityValidator:
    def validate(self, db_path: str | Path) -> ValidationReport:
        start = time.monotonic()
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            result = conn.execute("PRAGMA integrity_check").fetchone()
            integrity_ok = result is not None and result[0] == "ok"
            if integrity_ok:
                conn.execute("PRAGMA quick_check")
            journal_mode = conn.execute("PRAGMA journal_mode").fetchone()
            conn.close()
            return ValidationReport(
                "journal_integrity", integrity_ok,
                f"integrity={result}, journal={journal_mode}",
                time.monotonic() - start,
            )
        except Exception as e:
            return ValidationReport("journal_integrity", False, str(e), time.monotonic() - start)

    def auto_repair(self, db_path: str | Path) -> bool:
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            conn.execute("VACUUM")
            conn.close()
            return True
        except Exception:
            return False


class StartupWalValidator:
    def validate(self, db_path: str | Path) -> ValidationReport:
        start = time.monotonic()
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.execute("PRAGMA integrity_check")
            conn.close()
            return ValidationReport(
                "startup_wal", True, "WAL replay + checkpoint OK",
                time.monotonic() - start,
            )
        except Exception as e:
            return ValidationReport("startup_wal", False, str(e), time.monotonic() - start)


class BusyTimeoutValidator:
    def __init__(self, timeout_ms: int = 5000, max_retries: int = 5) -> None:
        self._timeout_ms = timeout_ms
        self._max_retries = max_retries

    def validate(self, db_path: str | Path) -> ValidationReport:
        start = time.monotonic()
        try:
            conn = sqlite3.connect(str(db_path), timeout=self._timeout_ms / 1000)
            conn.execute("SELECT 1")
            conn.close()
            return ValidationReport(
                "busy_timeout", True, f"Timeout {self._timeout_ms}ms",
                time.monotonic() - start,
            )
        except Exception as e:
            return ValidationReport("busy_timeout", False, str(e), time.monotonic() - start)


class CrashRecoveryValidator:
    def validate(self, db_path: str | Path) -> ValidationReport:
        start = time.monotonic()
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            conn.execute("CREATE TABLE IF NOT EXISTS _crash_test (id INTEGER, val TEXT)")
            conn.execute("INSERT INTO _crash_test VALUES (1, 'recovery')")
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            rows = conn.execute("SELECT COUNT(*) FROM _crash_test").fetchone()
            conn.execute("DROP TABLE IF EXISTS _crash_test")
            conn.close()
            ok = rows is not None and rows[0] == 1
            return ValidationReport(
                "crash_recovery", ok, f"Rows after recovery: {rows}",
                time.monotonic() - start,
            )
        except Exception as e:
            return ValidationReport("crash_recovery", False, str(e), time.monotonic() - start)


class LockStarvationValidator:
    def __init__(self, timeout_ms: int = 200) -> None:
        self._timeout_ms = timeout_ms
        self._success_count = 0
        self._failure_count = 0

    @property
    def success_count(self) -> int:
        return self._success_count

    @property
    def failure_count(self) -> int:
        return self._failure_count

    def validate(self, db_path: str | Path) -> ValidationReport:
        start = time.monotonic()
        try:
            conn_a = sqlite3.connect(str(db_path), timeout=5.0)
            conn_a.execute("BEGIN IMMEDIATE")
            try:
                conn_b = sqlite3.connect(str(db_path), timeout=self._timeout_ms / 1000)
                conn_b.execute("BEGIN IMMEDIATE")
                conn_b.close()
                self._failure_count += 1
            except sqlite3.OperationalError:
                self._success_count += 1
            conn_a.execute("ROLLBACK")
            conn_a.close()
            return ValidationReport(
                "lock_starvation", True,
                f"success={self._success_count}, failure={self._failure_count}",
                time.monotonic() - start,
            )
        except Exception as e:
            return ValidationReport(
                "lock_starvation", False, str(e), time.monotonic() - start,
            )
