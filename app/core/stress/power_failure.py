from __future__ import annotations

import hashlib
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PowerReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool] = field(default_factory=dict)

    def success(self, detail: str) -> PowerReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> PowerReport:
        self.passed = False
        self.detail = detail
        return self


class PowerFailureValidator:
    def __init__(self, work_dir: Path) -> None:
        self._work = work_dir
        self._work.mkdir(parents=True, exist_ok=True)

    def _db(self, name: str) -> Path:
        return self._work / name

    def _wal_path(self, db_path: Path) -> Path:
        return db_path.with_suffix(db_path.suffix + "-wal")

    def _count(self, path: Path, table: str = "t") -> int:
        try:
            conn = sqlite3.connect(str(path))
            c = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            conn.close()
            return c
        except Exception:
            return -1

    def _integrity(self, path: Path) -> bool:
        try:
            conn = sqlite3.connect(str(path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            return row is not None and row[0] == "ok"
        except Exception:
            return False

    def _make_db(self, path: Path, table: str = "t") -> sqlite3.Connection:
        conn = sqlite3.connect(str(path), timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table} "
                      "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                      "v TEXT, ts REAL)")
        conn.commit()
        return conn

    # 1 — Forced shutdown during isolated WAL write
    def validate_forced_shutdown_wal_write(self) -> PowerReport:
        start = time.monotonic()
        r = PowerReport(scenario="forced_shutdown_wal_write")
        try:
            db = self._db("forced_shutdown.db")
            conn = self._make_db(db, "t")
            for i in range(20):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"pre_{i}",))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            pre_count = self._count(db)
            # simulate WAL write without commit then "crash"
            conn.execute("INSERT INTO t (v) VALUES ('uncommitted')")
            conn.execute("INSERT INTO t (v) VALUES ('uncommitted2')")
            conn.close()
            # WAL wipe simulates power loss before commit
            wal = self._wal_path(db)
            if wal.exists():
                wal.unlink()
            conn2 = sqlite3.connect(str(db), timeout=30)
            conn2.execute("PRAGMA integrity_check").fetchone()
            post_count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM t"
            ).fetchone()[0]
            conn2.close()
            integrity = self._integrity(db)
            r.checks["pre_count"] = pre_count == 20
            r.checks["no_growth"] = post_count == 20
            r.checks["integrity"] = integrity
            if integrity and post_count == 20:
                return r.success(
                    f"forced shutdown: {post_count}/{pre_count} rows survived"
                )
            return r.fail(f"integrity={integrity}, post={post_count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 2 — Interrupted checkpoint replay
    def validate_interrupted_checkpoint_replay(self) -> PowerReport:
        start = time.monotonic()
        r = PowerReport(scenario="interrupted_checkpoint_replay")
        try:
            db = self._db("interrupted_ckpt.db")
            conn = self._make_db(db, "t")
            for i in range(100):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"ckpt_{i}",))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            wal = self._wal_path(db)
            if wal.exists():
                with open(wal, "w") as f:
                    f.truncate(0)
            conn.close()
            count = self._count(db)
            integrity = self._integrity(db)
            r.checks["count"] = count == 100
            r.checks["integrity"] = integrity
            if integrity and count == 100:
                return r.success(f"interrupted ckpt: {count} rows, integrity OK")
            return r.fail(f"count={count}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 3 — Unsafe power-loss simulation (writes lost)
    def validate_unsafe_power_loss(self) -> PowerReport:
        start = time.monotonic()
        r = PowerReport(scenario="unsafe_power_loss")
        try:
            db = self._db("power_loss.db")
            conn = self._make_db(db, "t")
            for i in range(50):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"safe_{i}",))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            # Unsafe writes that may not survive
            for i in range(10):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"unsafe_{i}",))
            conn.close()
            wal = self._wal_path(db)
            if wal.exists():
                wal.unlink()
            count = self._count(db)
            integrity = self._integrity(db)
            r.checks["safe_survived"] = count >= 50
            r.checks["integrity_ok"] = integrity
            if integrity and count >= 50:
                return r.success(
                    f"power loss: {count} safe rows survived"
                )
            return r.fail(f"count={count}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 4 — Queue replay interruption
    def validate_queue_replay_interruption(self) -> PowerReport:
        start = time.monotonic()
        r = PowerReport(scenario="queue_replay_interruption")
        try:
            db = self._db("queue_interrupt.db")
            conn = self._make_db(db, "queue")
            for i in range(80):
                conn.execute(
                    "INSERT INTO queue (v) VALUES (?)",
                    (f"queue_item_{i}",),
                )
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            conn.close()
            wal = self._wal_path(db)
            if wal.exists():
                wal.unlink()
            conn2 = sqlite3.connect(str(db), timeout=30)
            conn2.execute("PRAGMA journal_mode=WAL")
            recovered = conn2.execute(
                "SELECT COUNT(*) FROM queue"
            ).fetchone()[0]
            conn2.close()
            integrity = self._integrity(db)
            r.checks["recovered"] = recovered >= 75
            r.checks["integrity"] = integrity
            if integrity and recovered >= 75:
                return r.success(
                    f"queue interrupt: {recovered}/80 recovered"
                )
            return r.fail(f"recovered={recovered}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 5 — Archive replay interruption
    def validate_archive_replay_interruption(self) -> PowerReport:
        start = time.monotonic()
        r = PowerReport(scenario="archive_replay_interruption")
        try:
            db = self._db("archive_interrupt.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS archive ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "snapshot_id TEXT, checksum TEXT)"
            )
            for i in range(60):
                ck = hashlib.sha256(f"arch_{i}".encode()).hexdigest()
                conn.execute(
                    "INSERT INTO archive (snapshot_id, checksum) VALUES (?,?)",
                    (f"arch_{i}", ck),
                )
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
            wal = self._wal_path(db)
            if wal.exists():
                wal.unlink()
            conn2 = sqlite3.connect(str(db), timeout=30)
            conn2.execute("PRAGMA journal_mode=WAL")
            recovered = conn2.execute(
                "SELECT COUNT(*) FROM archive"
            ).fetchone()[0]
            conn2.close()
            integrity = self._integrity(db)
            r.checks["recovered"] = recovered == 60
            r.checks["integrity"] = integrity
            if integrity and recovered == 60:
                return r.success(f"archive interrupt: {recovered}/60 recovered")
            return r.fail(f"recovered={recovered}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 6 — Recovery-loop validation (repeated open/close)
    def validate_recovery_loop(self) -> PowerReport:
        start = time.monotonic()
        r = PowerReport(scenario="recovery_loop")
        try:
            db = self._db("recovery_loop.db")
            for cycle in range(10):
                conn = sqlite3.connect(str(db), timeout=30)
                conn.execute("PRAGMA journal_mode=WAL")
                if cycle == 0:
                    conn.execute(
                        "CREATE TABLE IF NOT EXISTS t ("
                        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                        "cycle INTEGER, ts REAL)"
                    )
                for i in range(20):
                    conn.execute(
                        "INSERT INTO t (cycle) VALUES (?)", (cycle,)
                    )
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
                conn.close()
                wal = self._wal_path(db)
                if wal.exists():
                    wal.unlink()
            integrity = self._integrity(db)
            total = self._count(db)
            r.checks["total"] = total == 200
            r.checks["integrity"] = integrity
            if integrity and total == 200:
                return r.success(f"recovery loop: {total} across {10} cycles")
            return r.fail(f"total={total}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 7 — Rollback continuity replay
    def validate_rollback_continuity_replay(self) -> PowerReport:
        start = time.monotonic()
        r = PowerReport(scenario="rollback_continuity_replay")
        try:
            db = self._db("rollback_continuity.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS t ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "seq INTEGER, state TEXT)"
            )
            for i in range(25):
                conn.execute(
                    "INSERT INTO t (seq, state) VALUES (?,?)",
                    (i, f"state_{i}"),
                )
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            base_count = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            conn.close()
            for rollback_cycle in range(3):
                wal = self._wal_path(db)
                if wal.exists():
                    wal.unlink()
                conn = sqlite3.connect(str(db), timeout=30)
                conn.execute("PRAGMA journal_mode=WAL")
                for i in range(5):
                    conn.execute(
                        "INSERT INTO t (seq, state) VALUES (?,?)",
                        (base_count + rollback_cycle * 5 + i,
                         f"rollback_{rollback_cycle}_{i}"),
                    )
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
            final = self._count(db)
            integrity = self._integrity(db)
            r.checks["final_count"] = final == 40
            r.checks["integrity"] = integrity
            if integrity and final == 40:
                return r.success(f"rollback continuity: {final} rows, integrity OK")
            return r.fail(f"final={final}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 8 — Partial-write recovery
    def validate_partial_write_recovery(self) -> PowerReport:
        start = time.monotonic()
        r = PowerReport(scenario="partial_write_recovery")
        try:
            db = self._db("partial_write.db")
            conn = self._make_db(db, "t")
            for i in range(30):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"base_{i}",))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.execute("INSERT INTO t (v) VALUES ('partial')")
            conn.execute("INSERT INTO t (v) VALUES ('partial2')")
            conn.execute("INSERT INTO t (v) VALUES ('partial3')")
            conn.close()
            wal = self._wal_path(db)
            if wal.exists():
                with open(wal, "r+b") as f:
                    data = f.read()
                    f.seek(0)
                    f.write(data[:len(data)//2])
                    f.truncate()
            count = self._count(db)
            integrity = self._integrity(db)
            r.checks["recovered"] = count >= 30
            r.checks["integrity"] = integrity
            if integrity:
                return r.success(f"partial write: {count} rows recovered")
            return r.fail(f"count={count}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 9 — Startup repair continuity
    def validate_startup_repair_continuity(self) -> PowerReport:
        start = time.monotonic()
        r = PowerReport(scenario="startup_repair_continuity")
        try:
            db = self._db("startup_repair.db")
            conn = self._make_db(db, "t")
            for i in range(40):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"startup_{i}",))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
            for _ in range(5):
                wal = self._wal_path(db)
                if wal.exists():
                    wal.unlink()
                conn = sqlite3.connect(str(db), timeout=30)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA integrity_check").fetchone()
                conn.close()
            integrity = self._integrity(db)
            final = self._count(db)
            r.checks["final"] = final == 40
            r.checks["integrity"] = integrity
            if integrity and final == 40:
                return r.success(f"startup repair: {final} rows after 5 cycles")
            return r.fail(f"final={final}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 10 — Deterministic crash replay
    def validate_deterministic_crash_replay(self) -> PowerReport:
        start = time.monotonic()
        r = PowerReport(scenario="deterministic_crash_replay")
        try:
            results: list[int] = []
            for run in range(3):
                db = self._db(f"crash_det_{run}.db")
                conn = self._make_db(db, "t")
                for i in range(20):
                    conn.execute("INSERT INTO t (v) VALUES (?)",
                                 (f"det_{run}_{i}",))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
                wal = self._wal_path(db)
                if wal.exists():
                    wal.unlink()
                count = self._count(db)
                results.append(count)
            stable = len(set(results)) == 1
            integrity = all(
                self._integrity(self._db(f"crash_det_{r}.db"))
                for r in range(3)
            )
            r.checks["deterministic"] = stable
            r.checks["all_integrity"] = integrity
            if stable and integrity:
                return r.success(
                    f"deterministic crash: {results[0]} rows, 3/3 stable"
                )
            return r.fail(f"results={results}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[PowerReport]:
        return [
            self.validate_forced_shutdown_wal_write(),
            self.validate_interrupted_checkpoint_replay(),
            self.validate_unsafe_power_loss(),
            self.validate_queue_replay_interruption(),
            self.validate_archive_replay_interruption(),
            self.validate_recovery_loop(),
            self.validate_rollback_continuity_replay(),
            self.validate_partial_write_recovery(),
            self.validate_startup_repair_continuity(),
            self.validate_deterministic_crash_replay(),
        ]
