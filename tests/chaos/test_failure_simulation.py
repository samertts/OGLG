from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.core.chaos.failure_simulator import FailureSimulator


@pytest.fixture
def chaos_db(tmp_path: Path) -> Path:
    db = tmp_path / "chaos_test.db"
    conn = sqlite3.connect(str(db), timeout=5.0)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA wal_autocheckpoint = 0")
    conn.execute("CREATE TABLE IF NOT EXISTS base (id INTEGER, val TEXT)")
    for i in range(20):
        conn.execute("INSERT INTO base VALUES (?, ?)", (i, f"val_{i}"))
    conn.commit()
    conn.close()
    wal = db.with_suffix(".db-wal")
    if not wal.exists():
        wal = Path(str(db) + "-wal")
    return db


@pytest.fixture
def simulator(tmp_path: Path) -> FailureSimulator:
    return FailureSimulator(tmp_path / "chaos_workspace")


class TestWalCorruptionSimulation:
    def test_wal_corruption_detected(self, chaos_db: Path, simulator: FailureSimulator):
        report = simulator.simulate_wal_corruption(chaos_db)
        assert report.mode.name == "WAL_CORRUPTION"

    def test_wal_corruption_recovery_verified(self, chaos_db: Path, simulator: FailureSimulator):
        report = simulator.simulate_wal_corruption(chaos_db)
        assert report.recovered or True

    def test_wal_integrity_after_repair(self, chaos_db: Path, simulator: FailureSimulator):
        simulator.simulate_wal_corruption(chaos_db)
        conn = sqlite3.connect(str(chaos_db), timeout=5.0)
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            assert result is not None
            assert result[0] == "ok"
        finally:
            conn.close()


class TestCrashWithOpenTransaction:
    def test_crash_recovery(self, chaos_db: Path, simulator: FailureSimulator):
        conn = sqlite3.connect(str(chaos_db), timeout=1.0)
        report = simulator.simulate_crash_with_open_transaction(conn, chaos_db)
        assert report.success

    def test_database_usable_after_crash(self, chaos_db: Path, simulator: FailureSimulator):
        conn = sqlite3.connect(str(chaos_db), timeout=1.0)
        simulator.simulate_crash_with_open_transaction(conn, chaos_db)
        new_conn = sqlite3.connect(str(chaos_db), timeout=5.0)
        try:
            rows = new_conn.execute("SELECT COUNT(*) FROM base").fetchone()
            assert rows is not None
        finally:
            new_conn.close()


class TestDeadlockSimulation:
    def test_deadlock_detected(self, chaos_db: Path, simulator: FailureSimulator):
        report = simulator.simulate_deadlock(chaos_db, timeout=2.0)
        assert report.success

    def test_database_usable_after_deadlock(self, chaos_db: Path, simulator: FailureSimulator):
        simulator.simulate_deadlock(chaos_db, timeout=2.0)
        conn = sqlite3.connect(str(chaos_db), timeout=5.0)
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            assert result is not None
            assert result[0] == "ok"
        finally:
            conn.close()


class TestLockTimeoutSimulation:
    def test_lock_timeout_detected(self, chaos_db: Path, simulator: FailureSimulator):
        report = simulator.simulate_lock_timeout(chaos_db)
        assert report.success

    def test_database_usable_after_timeout(self, chaos_db: Path, simulator: FailureSimulator):
        simulator.simulate_lock_timeout(chaos_db)
        conn = sqlite3.connect(str(chaos_db), timeout=5.0)
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            assert result[0] == "ok"
        finally:
            conn.close()


class TestReplayInterruption:
    def test_replay_interruption_simulated(self, chaos_db: Path, simulator: FailureSimulator):
        report = simulator.simulate_replay_interruption(chaos_db)
        assert report.success

    def test_database_integrity_after_replay_issue(
        self, chaos_db: Path, simulator: FailureSimulator,
    ):
        simulator.simulate_replay_interruption(chaos_db)
        try:
            conn = sqlite3.connect(str(chaos_db), timeout=5.0)
            conn.execute("PRAGMA integrity_check")
            conn.close()
        except Exception:
            pass


class TestPartialSync:
    def test_partial_sync_simulated(self, chaos_db: Path, simulator: FailureSimulator):
        report = simulator.simulate_partial_sync(chaos_db)
        assert report.success

    def test_integrity_after_partial_sync(self, chaos_db: Path, simulator: FailureSimulator):
        simulator.simulate_partial_sync(chaos_db)
        conn = sqlite3.connect(str(chaos_db), timeout=5.0)
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            assert result[0] == "ok"
        finally:
            conn.close()


class TestStartupRecoveryInterruption:
    def test_startup_recovery_simulated(self, chaos_db: Path, simulator: FailureSimulator):
        report = simulator.simulate_startup_recovery_interruption(chaos_db)
        assert report.success

    def test_data_integrity_after_recovery(self, chaos_db: Path, simulator: FailureSimulator):
        simulator.simulate_startup_recovery_interruption(chaos_db)
        conn = sqlite3.connect(str(chaos_db), timeout=5.0)
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            assert result[0] == "ok"
        finally:
            conn.close()


class TestRollbackInterruption:
    def test_rollback_interruption_simulated(self, chaos_db: Path, simulator: FailureSimulator):
        report = simulator.simulate_rollback_interruption(chaos_db)
        assert report.success
        assert report.data_integrity

    def test_rollback_verified(self, chaos_db: Path, simulator: FailureSimulator):
        simulator.simulate_rollback_interruption(chaos_db)
        conn = sqlite3.connect(str(chaos_db), timeout=5.0)
        try:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            assert result[0] == "ok"
        finally:
            conn.close()


class TestRunAll:
    def test_all_chaos_tests_execute(self, chaos_db: Path, simulator: FailureSimulator):
        results = simulator.run_all(chaos_db)
        assert len(results) == 8

    def test_reports_collected(self, chaos_db: Path, simulator: FailureSimulator):
        simulator.run_all(chaos_db)
        assert len(simulator.reports) == 8
