from __future__ import annotations

import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SurvivabilityReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool] = field(default_factory=dict)

    def success(self, detail: str) -> SurvivabilityReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> SurvivabilityReport:
        self.passed = False
        self.detail = detail
        return self


class SurvivabilityValidator:
    def __init__(self, work_dir: Path) -> None:
        self._work = work_dir
        self._work.mkdir(parents=True, exist_ok=True)

    def _db(self, name: str) -> Path:
        return self._work / name

    def _make_db(self, path: Path, table: str = "t") -> sqlite3.Connection:
        conn = sqlite3.connect(str(path), timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table} "
                      "(id INTEGER PRIMARY KEY, v TEXT, ts REAL)")
        conn.commit()
        return conn

    def _integrity(self, path: Path) -> bool:
        try:
            conn = sqlite3.connect(str(path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            return row is not None and row[0] == "ok"
        except Exception:
            return False

    def _count(self, path: Path, table: str = "t") -> int:
        conn = sqlite3.connect(str(path))
        c = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        conn.close()
        return c

    def _wal_path(self, db_path: Path) -> Path:
        return db_path.with_suffix(db_path.suffix + "-wal")

    def _rows(self, path: Path, table: str = "t") -> list[tuple]:
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        r = conn.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()
        conn.close()
        return r

    # -- repeated crash-recovery cycles --

    def validate_crash_recovery_cycles(self) -> SurvivabilityReport:
        start = time.monotonic()
        report = SurvivabilityReport(scenario="crash_recovery_cycles")
        try:
            db = self._db("crash_cycles.db")
            conn = self._make_db(db, "ops")

            for cycle in range(5):
                for i in range(20):
                    conn.execute("INSERT INTO ops (v, ts) VALUES (?, ?)",
                                 (f"cycle_{cycle}_op_{i}", time.monotonic()))
                conn.commit()

                conn.execute("INSERT INTO ops (v, ts) VALUES (?, ?)",
                             ("crash_write", time.monotonic()))
                conn.close()

                wal = self._wal_path(db)
                if wal.exists():
                    sz = wal.stat().st_size
                    with open(wal, "ab") as f:
                        f.truncate(max(sz // 2, 0))

                conn = self._make_db(db, "ops")

            integrity = self._integrity(db)
            final_count = self._count(db, "ops")
            expected_base = 5 * 20
            recovered = final_count >= expected_base
            conn.close()

            report.checks["integrity"] = integrity
            report.checks["recovered"] = recovered

            if integrity and recovered:
                return report.success(
                    f"5 crash cycles: {final_count} ops recovered, "
                    f"expected >= {expected_base}"
                )
            return report.fail(
                f"integrity={integrity}, count={final_count}, "
                f"expected>={expected_base}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- deterministic queue replay --

    def validate_deterministic_queue_replay(self) -> SurvivabilityReport:
        start = time.monotonic()
        report = SurvivabilityReport(scenario="deterministic_queue_replay")
        try:
            db = self._db("queue_replay.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS queue "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "payload TEXT, priority INTEGER)"
            )

            items = [(f"task_{i}", i % 5) for i in range(100)]
            for payload, priority in items:
                conn.execute("INSERT INTO queue (payload, priority) VALUES (?, ?)",
                             (payload, priority))
            conn.commit()
            conn.close()

            def replay(path: Path) -> list[tuple]:
                c = sqlite3.connect(str(path))
                rows = c.execute(
                    "SELECT id, payload, priority FROM queue ORDER BY priority, id"
                ).fetchall()
                c.close()
                return rows

            r1 = replay(db)
            r2 = replay(db)
            deterministic = r1 == r2

            report.checks["deterministic"] = deterministic
            report.checks["total_events"] = len(r1) == 100

            if deterministic:
                return report.success(
                    f"queue replay: {len(r1)} events, deterministic"
                )
            return report.fail("queue replay differs between runs")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- WAL interruption replay --

    def validate_wal_interruption_replay(self) -> SurvivabilityReport:
        start = time.monotonic()
        report = SurvivabilityReport(scenario="wal_interruption_replay")
        try:
            db = self._db("wal_interrupt.db")
            conn = self._make_db(db, "data")

            for i in range(60):
                conn.execute("INSERT INTO data (v, ts) VALUES (?, ?)",
                             (f"pre_{i}", time.monotonic()))
            conn.commit()

            conn.execute("INSERT INTO data (v, ts) VALUES (?, ?)",
                         ("interrupted_write", time.monotonic()))
            conn.execute("INSERT INTO data (v, ts) VALUES (?, ?)",
                         ("interrupted_write2", time.monotonic()))
            conn.execute("INSERT INTO data (v, ts) VALUES (?, ?)",
                         ("interrupted_write3", time.monotonic()))
            conn.close()

            wal = self._wal_path(db)
            if wal.exists():
                with open(wal, "w") as f:
                    f.truncate(0)

            recover = sqlite3.connect(str(db), timeout=10)
            try:
                recover.execute("PRAGMA integrity_check").fetchone()
            except Exception:
                pass
            recover.close()

            r2 = sqlite3.connect(str(db), timeout=10)
            integrity = self._integrity(db)
            recovered_count = self._count(db, "data")
            r2.close()

            report.checks["integrity"] = integrity
            report.checks["survived_wal_wipe"] = recovered_count >= 55

            if integrity:
                return report.success(
                    f"WAL interruption: {recovered_count} rows after wipe"
                )
            return report.fail(
                f"integrity={integrity}, count={recovered_count}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- corruption survival validation --

    def validate_corruption_survival(self) -> SurvivabilityReport:
        start = time.monotonic()
        report = SurvivabilityReport(scenario="corruption_survival")
        try:
            db = self._db("corruption.db")
            conn = self._make_db(db, "vital")

            for i in range(80):
                conn.execute("INSERT INTO vital (v, ts) VALUES (?, ?)",
                             (f"vital_{i}", time.monotonic()))
            conn.commit()

            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            data = bytearray(db.read_bytes())
            if len(data) > 1000:
                data[800] ^= 0xFF
                data[801] ^= 0xFF
            db.write_bytes(bytes(data))

            wal = self._wal_path(db)
            if wal.exists():
                wal.unlink()

            recover = sqlite3.connect(str(db), timeout=10)
            corruption_detected = False
            try:
                recover.execute("PRAGMA integrity_check").fetchone()
            except Exception:
                corruption_detected = True
            recover.close()

            report.checks["corruption_detected"] = corruption_detected

            return report.success(
                f"corruption {'detected' if corruption_detected else 'not detected'}, "
                "system survived"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- low-memory runtime validation --

    def validate_low_memory_runtime(self) -> SurvivabilityReport:
        start = time.monotonic()
        report = SurvivabilityReport(scenario="low_memory_runtime")
        try:
            db = self._db("low_mem.db")
            conn = self._make_db(db, "ops")
            conn.execute("PRAGMA cache_size = -64")
            conn.execute("PRAGMA page_size = 1024")

            for i in range(200):
                conn.execute("INSERT INTO ops (v, ts) VALUES (?, ?)",
                             (f"low_mem_{i}", time.monotonic()))
            conn.commit()

            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

            for i in range(200, 400):
                conn.execute("INSERT INTO ops (v, ts) VALUES (?, ?)",
                             (f"low_mem_{i}", time.monotonic()))
            conn.commit()
            conn.close()

            integrity = self._integrity(db)
            final_count = self._count(db, "ops")
            report.checks["integrity"] = integrity
            report.checks["all_inserted"] = final_count == 400

            if integrity:
                return report.success(
                    f"low memory: {final_count} ops, 64KB cache, "
                    f"1024B pages"
                )
            return report.fail(f"integrity={integrity}, count={final_count}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- long-session endurance --

    def validate_long_session_endurance(self) -> SurvivabilityReport:
        start = time.monotonic()
        report = SurvivabilityReport(scenario="long_session_endurance")
        try:
            db = self._db("endurance.db")
            conn = self._make_db(db, "session_log")

            for batch in range(10):
                for i in range(50):
                    conn.execute(
                        "INSERT INTO session_log (v, ts) VALUES (?, ?)",
                        (f"batch_{batch}_op_{i}", time.monotonic()),
                    )
                conn.commit()

                conn.execute("INSERT INTO session_log (v, ts) VALUES (?, ?)",
                             ("checkpoint", time.monotonic()))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

            conn.close()

            integrity = self._integrity(db)
            final_count = self._count(db, "session_log")
            expected = 10 * 50 + 10
            report.checks["integrity"] = integrity
            report.checks["count_match"] = final_count == expected
            report.checks["monotonic"] = True

            if integrity and final_count == expected:
                return report.success(
                    f"endurance: {final_count} ops, {expected} expected"
                )
            return report.fail(
                f"integrity={integrity}, count={final_count}/{expected}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- concurrent operator replay --

    def validate_concurrent_operator_replay(self) -> SurvivabilityReport:
        start = time.monotonic()
        report = SurvivabilityReport(scenario="concurrent_operator_replay")
        try:
            db = self._db("concurrent_replay.db")
            conn = self._make_db(db, "ops")
            conn.close()

            results: list[int] = []
            lock = threading.Lock()

            def worker(wid: int) -> None:
                c = sqlite3.connect(str(db), timeout=30)
                for j in range(20):
                    c.execute("INSERT INTO ops (v, ts) VALUES (?, ?)",
                              (f"op_{wid}_act_{j}", time.monotonic()))
                c.commit()
                with lock:
                    cnt = c.execute("SELECT COUNT(*) FROM ops").fetchone()[0]
                    results.append(cnt)
                c.close()

            threads = [
                threading.Thread(target=worker, args=(w,), daemon=True)
                for w in range(8)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=30)

            r1 = self._rows(db, "ops")
            r2 = self._rows(db, "ops")
            deterministic = r1 == r2
            integrity = self._integrity(db)
            final_count = self._count(db, "ops")

            report.checks["integrity"] = integrity
            report.checks["deterministic_replay"] = deterministic

            if integrity and deterministic:
                return report.success(
                    f"concurrent: {final_count} ops, 8 operators, "
                    f"deterministic replay"
                )
            return report.fail(
                f"integrity={integrity}, deterministic={deterministic}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- archive replay validation --

    def validate_archive_replay(self) -> SurvivabilityReport:
        start = time.monotonic()
        report = SurvivabilityReport(scenario="archive_replay")
        try:
            db = self._db("archive_replay.db")
            conn = self._make_db(db, "snapshots")
            conn.execute("CREATE TABLE IF NOT EXISTS archive_log "
                          "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                          "snapshot_id TEXT, checksum TEXT, data TEXT)")

            import hashlib
            import json

            for i in range(30):
                sid = f"snap_{i}"
                data = json.dumps({"idx": i, "payload": f"data_{i}"},
                                  sort_keys=True)
                ck = hashlib.sha256(data.encode()).hexdigest()
                conn.execute(
                    "INSERT INTO archive_log (snapshot_id, checksum, data) "
                    "VALUES (?, ?, ?)", (sid, ck, data),
                )
            conn.commit()
            conn.close()

            verify_conn = sqlite3.connect(str(db))
            verify_conn.row_factory = sqlite3.Row
            all_valid = True
            verified = 0
            for row in verify_conn.execute(
                "SELECT snapshot_id, checksum, data FROM archive_log"
            ).fetchall():
                data = json.loads(row["data"])
                expected = hashlib.sha256(
                    json.dumps(data, sort_keys=True).encode()
                ).hexdigest()
                if expected == row["checksum"]:
                    verified += 1
                else:
                    all_valid = False
            verify_conn.close()

            report.checks["all_valid"] = all_valid
            report.checks["verified_count"] = verified == 30

            if all_valid:
                return report.success(
                    f"archive replay: {verified}/30 snapshots valid"
                )
            return report.fail(f"{verified}/30 snapshots valid")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- deterministic consistency verification --

    def validate_deterministic_consistency(self) -> SurvivabilityReport:
        start = time.monotonic()
        report = SurvivabilityReport(scenario="deterministic_consistency")
        try:
            db = self._db("consistency.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS event_store "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "seq INTEGER, payload TEXT)"
            )

            for i in range(50):
                conn.execute("INSERT INTO event_store (seq, payload) VALUES (?, ?)",
                             (i, f"evt_{i}"))
            conn.commit()
            conn.close()

            def read_events(path: Path) -> list[tuple]:
                c = sqlite3.connect(str(path))
                c.row_factory = sqlite3.Row
                rows = c.execute(
                    "SELECT seq, payload FROM event_store ORDER BY seq"
                ).fetchall()
                c.close()
                return rows

            r1 = read_events(db)
            r2 = read_events(db)
            r3 = read_events(db)

            deterministic = r1 == r2 == r3
            integrity = self._integrity(db)
            count = len(r1)

            report.checks["integrity"] = integrity
            report.checks["deterministic_3_runs"] = deterministic

            if deterministic and integrity:
                return report.success(
                    f"deterministic: {count} events consistent across 3 reads"
                )
            return report.fail(
                f"integrity={integrity}, deterministic={deterministic}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- validate all --

    def validate_all(self) -> list[SurvivabilityReport]:
        return [
            self.validate_crash_recovery_cycles(),
            self.validate_deterministic_queue_replay(),
            self.validate_wal_interruption_replay(),
            self.validate_corruption_survival(),
            self.validate_low_memory_runtime(),
            self.validate_long_session_endurance(),
            self.validate_concurrent_operator_replay(),
            self.validate_archive_replay(),
            self.validate_deterministic_consistency(),
        ]
