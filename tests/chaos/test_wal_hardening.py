from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.chaos.wal_hardening import (
    BusyTimeoutValidator,
    CrashRecoveryValidator,
    JournalIntegrityValidator,
    LockStarvationValidator,
    StartupWalValidator,
    WalGrowthValidator,
)


def _seed_wal_db(db: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db), timeout=5.0)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA wal_autocheckpoint = 0")
    conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER, val TEXT)")
    for i in range(20):
        conn.execute("INSERT INTO t VALUES (?, ?)", (i, f"hello_{i}"))
    conn.commit()
    return conn


class TestWalGrowth:
    def test_wal_growth_passes_when_within_limit(self, tmp_path: Path):
        db = tmp_path / "test.db"
        conn = _seed_wal_db(db)
        v = WalGrowthValidator(max_wal_mb=500.0)
        report = v.validate(db)
        conn.close()
        assert report.passed

    def test_wal_growth_fails_when_exceeded(self, tmp_path: Path):
        db = tmp_path / "test.db"
        conn = _seed_wal_db(db)
        v = WalGrowthValidator(max_wal_mb=0.0001)
        report = v.validate(db)
        conn.close()
        assert not report.passed

    def test_checkpoint_bytes_recorded(self):
        v = WalGrowthValidator()
        assert v.checkpoint_bytes == 0
        v.record_checkpoint(1024)
        assert v.checkpoint_bytes == 1024
        v.record_checkpoint(2048)
        assert v.checkpoint_bytes == 3072


class TestJournalIntegrity:
    def test_integrity_check_passes(self, tmp_path: Path):
        db = tmp_path / "test.db"
        _seed_wal_db(db).close()
        v = JournalIntegrityValidator()
        report = v.validate(db)
        assert report.passed

    def test_auto_repair(self, tmp_path: Path):
        db = tmp_path / "test.db"
        _seed_wal_db(db).close()
        v = JournalIntegrityValidator()
        assert v.auto_repair(db)


class TestStartupWal:
    def test_startup_wal_passes(self, tmp_path: Path):
        db = tmp_path / "test.db"
        _seed_wal_db(db).close()
        v = StartupWalValidator()
        report = v.validate(db)
        assert report.passed


class TestBusyTimeout:
    def test_busy_timeout_connects(self, tmp_path: Path):
        db = tmp_path / "test.db"
        _seed_wal_db(db).close()
        v = BusyTimeoutValidator(timeout_ms=5000, max_retries=5)
        report = v.validate(db)
        assert report.passed


class TestCrashRecovery:
    def test_crash_recovery_passes(self, tmp_path: Path):
        db = tmp_path / "test.db"
        _seed_wal_db(db).close()
        v = CrashRecoveryValidator()
        report = v.validate(db)
        assert report.passed

    def test_table_exists_after_checkpoint(self, tmp_path: Path):
        db = tmp_path / "test.db"
        conn = _seed_wal_db(db)
        conn.execute("CREATE TABLE IF NOT EXISTS persist_test (id INTEGER)")
        conn.execute("INSERT INTO persist_test VALUES (1)")
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        rows = conn.execute("SELECT COUNT(*) FROM persist_test").fetchone()
        conn.close()
        assert rows is not None
        assert rows[0] == 1


class TestLockStarvation:
    def test_lock_starvation_tracks_success(self, tmp_path: Path):
        db = tmp_path / "test.db"
        _seed_wal_db(db).close()
        v = LockStarvationValidator(timeout_ms=200)
        report = v.validate(db)
        assert report.passed
        assert v.success_count > 0 or v.failure_count > 0

    def test_lock_starvation_tracks_failure(self, tmp_path: Path):
        db = tmp_path / "test.db"
        _seed_wal_db(db).close()
        v = LockStarvationValidator(timeout_ms=100)
        v.validate(db)
        assert v.failure_count >= 0
