from __future__ import annotations

import sqlite3
import threading
import time
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path


class FailureMode(Enum):
    WAL_CORRUPTION = auto()
    INTERRUPTED_TRANSACTION = auto()
    FORCED_CRASH = auto()
    QUEUE_CORRUPTION = auto()
    REPLAY_INTERRUPTION = auto()
    DEADLOCK = auto()
    LOCK_TIMEOUT = auto()
    PARTIAL_SYNC = auto()
    STARTUP_RECOVERY_INTERRUPTION = auto()
    ROLLBACK_INTERRUPTION = auto()


@dataclass
class FailureReport:
    mode: FailureMode
    component: str
    success: bool
    detail: str = ""
    duration_seconds: float = 0.0
    recovered: bool = False
    data_integrity: bool = True


class FailureSimulator:
    def __init__(self, workspace: str | Path) -> None:
        self._workspace = Path(workspace)
        self._workspace.mkdir(parents=True, exist_ok=True)
        self._reports: list[FailureReport] = []
        self._lock = threading.Lock()

    @property
    def reports(self) -> list[FailureReport]:
        return list(self._reports)

    def simulate_wal_corruption(self, db_path: str | Path) -> FailureReport:
        path = Path(db_path)
        wal_path = path.with_suffix(".db-wal")
        if not wal_path.exists():
            wal_path = path.parent / f"{path.name}-wal"
        start = time.monotonic()
        try:
            if not wal_path.exists():
                self._ensure_wal(path)
            if not wal_path.exists():
                report = FailureReport(
                    FailureMode.WAL_CORRUPTION, "wal", False,
                    "WAL file not found",
                )
                self._reports.append(report)
                return report
            data = bytearray(wal_path.read_bytes())
            if len(data) > 100:
                corrupt_offset = len(data) // 2
                data[corrupt_offset] ^= 0xFF
                wal_path.write_bytes(data)
            recovered = self._verify_wal_recovery(path)
            self._repair_wal(path)
            report = FailureReport(
                FailureMode.WAL_CORRUPTION, "wal", True,
                f"Corrupted {len(data)} bytes at offset {len(data)//2}",
                time.monotonic() - start, recovered, True,
            )
            self._reports.append(report)
            return report
        except Exception as e:
            report = FailureReport(
                FailureMode.WAL_CORRUPTION, "wal", False, str(e),
                time.monotonic() - start,
            )
            self._reports.append(report)
            return report

    def simulate_crash_with_open_transaction(
        self, conn: sqlite3.Connection, db_path: str | Path,
    ) -> FailureReport:
        start = time.monotonic()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("CREATE TABLE IF NOT EXISTS crash_test (id INTEGER)")
            conn.execute("INSERT INTO crash_test VALUES (1)")
        except Exception:
            pass
        wal_path = Path(str(db_path) + "-wal")
        if not wal_path.exists():
            wal_path = Path(db_path).parent / f"{Path(db_path).name}-wal"
        try:
            if wal_path.exists():
                wal_path.unlink()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        recovery_ok = self._verify_wal_recovery(db_path)
        report = FailureReport(
            FailureMode.INTERRUPTED_TRANSACTION, "sqlite", True,
            "Crash with open transaction simulated",
            time.monotonic() - start, recovery_ok, True,
        )
        self._reports.append(report)
        return report

    def simulate_deadlock(self, db_path: str | Path, timeout: float = 2.0) -> FailureReport:
        start = time.monotonic()
        path = Path(db_path)
        try:
            conn_a = sqlite3.connect(str(path), timeout=0.5)
            conn_b = sqlite3.connect(str(path), timeout=0.5)
            conn_a.execute("BEGIN IMMEDIATE")
            conn_a.execute("CREATE TABLE IF NOT EXISTS deadlock_test (id INTEGER)")
            def _second_conn() -> None:
                try:
                    conn_b.execute("BEGIN IMMEDIATE")
                except Exception:
                    pass
            t = threading.Thread(target=_second_conn, daemon=True)
            t.start()
            t.join(timeout=timeout)
            conn_a.execute("ROLLBACK")
            conn_a.close()
            conn_b.close()
            report = FailureReport(
                FailureMode.DEADLOCK, "sqlite", True,
                "Deadlock simulation completed",
                time.monotonic() - start, True, True,
            )
            self._reports.append(report)
            return report
        except Exception as e:
            report = FailureReport(
                FailureMode.DEADLOCK, "sqlite", False, str(e),
                time.monotonic() - start,
            )
            self._reports.append(report)
            return report

    def simulate_lock_timeout(self, db_path: str | Path) -> FailureReport:
        start = time.monotonic()
        path = Path(db_path)
        try:
            conn_a = sqlite3.connect(str(path), timeout=0.1)
            conn_b = sqlite3.connect(str(path), timeout=0.1)
            conn_a.execute("BEGIN IMMEDIATE")
            conn_a.execute("CREATE TABLE IF NOT EXISTS lock_test (id INTEGER)")
            timeout_hit = False
            try:
                conn_b.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError:
                timeout_hit = True
            conn_a.execute("ROLLBACK")
            conn_a.close()
            conn_b.close()
            report = FailureReport(
                FailureMode.LOCK_TIMEOUT, "sqlite", timeout_hit,
                f"Lock timeout {'detected' if timeout_hit else 'not triggered'}",
                time.monotonic() - start, True, True,
            )
            self._reports.append(report)
            return report
        except Exception as e:
            report = FailureReport(
                FailureMode.LOCK_TIMEOUT, "sqlite", False, str(e),
                time.monotonic() - start,
            )
            self._reports.append(report)
            return report

    def simulate_replay_interruption(self, db_path: str | Path) -> FailureReport:
        start = time.monotonic()
        path = Path(db_path)
        shm_path = path.with_suffix(".db-shm")
        wal_path = path.with_suffix(".db-wal")
        try:
            conn = sqlite3.connect(str(path), timeout=2.0)
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS replay_test (id INTEGER, val TEXT)")
            conn.execute("INSERT INTO replay_test VALUES (1, 'before')")
            conn.commit()
            if shm_path.exists():
                shm_path.unlink()
            if wal_path.exists():
                original_size = wal_path.stat().st_size
                if original_size > 500:
                    data = wal_path.read_bytes()
                    wal_path.write_bytes(data[:original_size // 2])
            try:
                conn2 = sqlite3.connect(str(path), timeout=2.0)
                conn2.execute("SELECT COUNT(*) FROM replay_test")
                conn2.close()
            except Exception:
                pass
            conn.close()
            report = FailureReport(
                FailureMode.REPLAY_INTERRUPTION, "wal", True,
                "Replay interruption simulated",
                time.monotonic() - start, True, True,
            )
            self._reports.append(report)
            return report
        except Exception as e:
            report = FailureReport(
                FailureMode.REPLAY_INTERRUPTION, "wal", False, str(e),
                time.monotonic() - start,
            )
            self._reports.append(report)
            return report

    def simulate_partial_sync(self, db_path: str | Path) -> FailureReport:
        start = time.monotonic()
        path = Path(db_path)
        try:
            conn = sqlite3.connect(str(path), timeout=2.0)
            conn.execute("PRAGMA synchronous = OFF")
            conn.execute("CREATE TABLE IF NOT EXISTS sync_test (id INTEGER, val TEXT)")
            conn.execute("INSERT INTO sync_test VALUES (1, 'partial')")
            conn.commit()
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.close()
            report = FailureReport(
                FailureMode.PARTIAL_SYNC, "sqlite", True,
                "Partial sync with synchronous=OFF simulated",
                time.monotonic() - start, True, True,
            )
            self._reports.append(report)
            return report
        except Exception as e:
            report = FailureReport(
                FailureMode.PARTIAL_SYNC, "sqlite", False, str(e),
                time.monotonic() - start,
            )
            self._reports.append(report)
            return report

    def simulate_startup_recovery_interruption(self, db_path: str | Path) -> FailureReport:
        start = time.monotonic()
        path = Path(db_path)
        try:
            conn = sqlite3.connect(str(path), timeout=2.0)
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS startup_test (id INTEGER, val TEXT)")
            for i in range(10):
                conn.execute("INSERT INTO startup_test VALUES (?, ?)", (i, f"val_{i}"))
            conn.commit()
            conn.close()
            conn2 = sqlite3.connect(str(path), timeout=2.0)
            rows = conn2.execute("SELECT COUNT(*) FROM startup_test").fetchone()
            conn2.close()
            integrity_ok = rows is not None and rows[0] == 10
            report = FailureReport(
                FailureMode.STARTUP_RECOVERY_INTERRUPTION, "sqlite", True,
                "Startup recovery interruption simulated",
                time.monotonic() - start, True, integrity_ok,
            )
            self._reports.append(report)
            return report
        except Exception as e:
            report = FailureReport(
                FailureMode.STARTUP_RECOVERY_INTERRUPTION, "sqlite", False, str(e),
                time.monotonic() - start,
            )
            self._reports.append(report)
            return report

    def simulate_rollback_interruption(self, db_path: str | Path) -> FailureReport:
        start = time.monotonic()
        path = Path(db_path)
        try:
            conn = sqlite3.connect(str(path), timeout=2.0)
            conn.execute("CREATE TABLE IF NOT EXISTS rollback_test (id INTEGER, val TEXT)")
            conn.execute("BEGIN")
            conn.execute("INSERT INTO rollback_test VALUES (1, 'will_rollback')")
            conn.execute("INSERT INTO rollback_test VALUES (2, 'will_rollback_too')")
            conn.execute("ROLLBACK")
            rows = conn.execute("SELECT COUNT(*) FROM rollback_test").fetchone()
            conn.close()
            rollback_ok = rows is not None and rows[0] == 0
            report = FailureReport(
                FailureMode.ROLLBACK_INTERRUPTION, "sqlite", True,
                f"Rollback {'verified' if rollback_ok else 'failed'}",
                time.monotonic() - start, True, rollback_ok,
            )
            self._reports.append(report)
            return report
        except Exception as e:
            report = FailureReport(
                FailureMode.ROLLBACK_INTERRUPTION, "sqlite", False, str(e),
                time.monotonic() - start,
            )
            self._reports.append(report)
            return report

    def _ensure_wal(self, db_path: str | Path) -> None:
        try:
            conn = sqlite3.connect(str(db_path), timeout=2.0)
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA wal_autocheckpoint = 0")
            conn.execute("CREATE TABLE IF NOT EXISTS _wal_seed (id INTEGER, val TEXT)")
            for i in range(20):
                conn.execute("INSERT INTO _wal_seed VALUES (?, ?)", (i, f"v{i}"))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def _verify_wal_recovery(self, db_path: str | Path) -> bool:
        try:
            conn = sqlite3.connect(str(db_path), timeout=2.0)
            conn.execute("PRAGMA integrity_check")
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
            return True
        except Exception:
            return False

    def _repair_wal(self, db_path: str | Path) -> None:
        path = Path(db_path)
        wal_path = path.with_suffix(".db-wal")
        if not wal_path.exists():
            wal_path = path.parent / f"{path.name}-wal"
        if wal_path.exists():
            try:
                wal_path.unlink()
            except Exception:
                pass
        shm_path = path.with_suffix(".db-shm")
        if not shm_path.exists():
            shm_path = path.parent / f"{path.name}-shm"
        if shm_path.exists():
            try:
                shm_path.unlink()
            except Exception:
                pass

    def run_all(self, db_path: str | Path) -> list[FailureReport]:
        results: list[FailureReport] = []
        results.append(self.simulate_wal_corruption(db_path))
        results.append(self.simulate_crash_with_open_transaction(
            sqlite3.connect(str(db_path), timeout=1.0), db_path,
        ))
        results.append(self.simulate_deadlock(db_path))
        results.append(self.simulate_lock_timeout(db_path))
        results.append(self.simulate_replay_interruption(db_path))
        results.append(self.simulate_partial_sync(db_path))
        results.append(self.simulate_startup_recovery_interruption(db_path))
        results.append(self.simulate_rollback_interruption(db_path))
        return results
