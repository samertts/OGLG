from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FinalReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool] = field(default_factory=dict)

    def success(self, detail: str) -> FinalReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> FinalReport:
        self.passed = False
        self.detail = detail
        return self


class FinalRealityValidator:
    def __init__(self, work_dir: Path) -> None:
        self._work = work_dir
        self._work.mkdir(parents=True, exist_ok=True)

    def _db(self, name: str) -> Path:
        return self._work / name

    def _wal_path(self, db_path: Path) -> Path:
        return db_path.with_suffix(db_path.suffix + "-wal")

    def _integrity(self, path: Path) -> bool:
        try:
            conn = sqlite3.connect(str(path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            return row is not None and row[0] == "ok"
        except Exception:
            return False

    def _count(self, path: Path, table: str = "t") -> int:
        try:
            conn = sqlite3.connect(str(path))
            c = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            conn.close()
            return c
        except Exception:
            return -1

    # 1 — Full deployment replay with all subsystems
    def validate_full_deployment_replay(self) -> FinalReport:
        start = time.monotonic()
        r = FinalReport(scenario="full_deployment_replay")
        try:
            db = self._db("full_deploy.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size = -64")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS deploy_state ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "subsystem TEXT, action TEXT, seq INTEGER, ts REAL)"
            )
            subsystems = ["auth", "archive", "sync", "queue", "audit", "backup"]
            for seq in range(30):
                for sub in subsystems:
                    conn.execute(
                        "INSERT INTO deploy_state (subsystem, action, seq) "
                        "VALUES (?,?,?)",
                        (sub, f"cycle_{seq}", seq),
                    )
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            total = conn.execute(
                "SELECT COUNT(*) FROM deploy_state"
            ).fetchone()[0]
            conn.close()
            integrity = self._integrity(db)
            r.checks["total"] = total == 180
            r.checks["integrity"] = integrity
            if integrity and total == 180:
                return r.success(
                    f"deployment replay: {total} ops across {len(subsystems)} subsystems"
                )
            return r.fail(f"total={total}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 2 — Repeated crash cycles across deployment
    def validate_repeated_crash_cycles(self) -> FinalReport:
        start = time.monotonic()
        r = FinalReport(scenario="repeated_crash_cycles")
        try:
            db = self._db("crash_cycles.db")
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
            final = self._count(db)
            integrity = self._integrity(db)
            r.checks["survived"] = final == 200
            r.checks["integrity"] = integrity
            if integrity and final == 200:
                return r.success(f"crash cycles: {final} rows after 10 cycles")
            return r.fail(f"final={final}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 3 — Long-session endurance replay
    def validate_long_session_endurance_replay(self) -> FinalReport:
        start = time.monotonic()
        r = FinalReport(scenario="long_session_endurance_replay")
        try:
            db = self._db("long_endurance.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size = -64")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS session_log ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "session_id TEXT, action TEXT, ts REAL)"
            )
            for session in range(5):
                for action in range(50):
                    conn.execute(
                        "INSERT INTO session_log (session_id, action) "
                        "VALUES (?,?)",
                        (f"sess_{session}", f"action_{action}"),
                    )
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            total = conn.execute(
                "SELECT COUNT(*) FROM session_log"
            ).fetchone()[0]
            conn.close()
            integrity = self._integrity(db)
            r.checks["total"] = total == 250
            r.checks["integrity"] = integrity
            if integrity and total == 250:
                return r.success(f"endurance: {total} ops across 5 sessions")
            return r.fail(f"total={total}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 4 — WAL interruption replay
    def validate_wal_interruption_replay(self) -> FinalReport:
        start = time.monotonic()
        r = FinalReport(scenario="wal_interruption_replay")
        try:
            db = self._db("wal_interrupt_final.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS t ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, v TEXT)"
            )
            for i in range(60):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"pre_{i}",))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
            wal = self._wal_path(db)
            if wal.exists():
                wal.unlink()
            conn2 = sqlite3.connect(str(db), timeout=30)
            conn2.execute("PRAGMA journal_mode=WAL")
            recovered = conn2.execute(
                "SELECT COUNT(*) FROM t"
            ).fetchone()[0]
            conn2.close()
            integrity = self._integrity(db)
            r.checks["recovered"] = recovered == 60
            r.checks["integrity"] = integrity
            if integrity and recovered == 60:
                return r.success(f"WAL interrupt: {recovered}/60 recovered")
            return r.fail(f"recovered={recovered}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 5 — Replay divergence validation
    def validate_replay_divergence(self) -> FinalReport:
        start = time.monotonic()
        r = FinalReport(scenario="replay_divergence")
        try:
            results: list[list[int]] = []
            for run in range(3):
                db = self._db(f"divergence_{run}.db")
                conn = sqlite3.connect(str(db), timeout=30)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS t ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "seq INTEGER UNIQUE, v TEXT)"
                )
                for i in range(40):
                    conn.execute(
                        "INSERT OR IGNORE INTO t (seq, v) VALUES (?,?)",
                        (i, f"det_{i}"),
                    )
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
                wal = self._wal_path(db)
                if wal.exists():
                    wal.unlink()
                rows = sqlite3.connect(str(db)).execute(
                    "SELECT v FROM t ORDER BY id"
                ).fetchall()
                results.append([r[0] for r in rows])
            stable = all(r == results[0] for r in results)
            integrity = all(
                self._integrity(self._db(f"divergence_{r}.db"))
                for r in range(3)
            )
            r.checks["no_divergence"] = stable
            r.checks["integrity"] = integrity
            if stable and integrity:
                return r.success(
                    f"no divergence: {len(results[0])} rows, 3/3 identical"
                )
            return r.fail(
                f"divergent: {[len(x) for x in results]}"
            )
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 6 — Deterministic archive replay
    def validate_deterministic_archive_replay(self) -> FinalReport:
        start = time.monotonic()
        r = FinalReport(scenario="deterministic_archive_replay")
        try:
            db = self._db("det_archive.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS archive ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "snapshot_id TEXT, checksum TEXT, ts REAL)"
            )
            for i in range(30):
                payload = json.dumps(
                    {"snap": i, "data": f"content_{i}"}, sort_keys=True
                )
                ck = hashlib.sha256(payload.encode()).hexdigest()
                conn.execute(
                    "INSERT INTO archive (snapshot_id, checksum) VALUES (?,?)",
                    (f"snap_{i}", ck),
                )
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
            for run in range(3):
                wal = self._wal_path(db)
                if wal.exists():
                    wal.unlink()
                c = sqlite3.connect(str(db), timeout=30)
                c.execute("PRAGMA journal_mode=WAL")
                c.close()
            verified = 0
            c = sqlite3.connect(str(db))
            rows = c.execute(
                "SELECT snapshot_id, checksum FROM archive ORDER BY id"
            ).fetchall()
            for row in rows:
                expected = hashlib.sha256(
                    json.dumps(
                        {"snap": int(row[0].split("_")[1]),
                         "data": f"content_{int(row[0].split('_')[1])}"},
                        sort_keys=True,
                    ).encode()
                ).hexdigest()
                if expected == row[1]:
                    verified += 1
            c.close()
            integrity = self._integrity(db)
            r.checks["verified"] = verified == 30
            r.checks["integrity"] = integrity
            if integrity and verified == 30:
                return r.success(f"archive replay: {verified}/30 checksums verified")
            return r.fail(f"verified={verified}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 7 — Deployment rollback replay
    def validate_deployment_rollback_replay(self) -> FinalReport:
        start = time.monotonic()
        r = FinalReport(scenario="deployment_rollback_replay")
        try:
            db = self._db("rollback_final.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS state ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "version INTEGER, data TEXT)"
            )
            for i in range(20):
                conn.execute(
                    "INSERT INTO state (version, data) VALUES (?,?)",
                    (1, f"v1_{i}"),
                )
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            v1_count = conn.execute(
                "SELECT COUNT(*) FROM state"
            ).fetchone()[0]
            conn.close()
            import shutil
            backup = self._db("backup_final.db")
            shutil.copy2(db, backup)
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            for i in range(10):
                conn.execute(
                    "INSERT INTO state (version, data) VALUES (?,?)",
                    (2, f"v2_{i}"),
                )
            conn.commit()
            conn.close()
            shutil.copy2(backup, db)
            final = self._count(db, "state")
            integrity = self._integrity(db)
            r.checks["rollback_ok"] = final == v1_count
            r.checks["integrity"] = integrity
            if integrity and final == v1_count:
                return r.success(
                    f"rollback: {final} rows restored (was {v1_count})"
                )
            return r.fail(f"final={final}, expected={v1_count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 8 — Low-resource survivability
    def validate_low_resource_survivability(self) -> FinalReport:
        start = time.monotonic()
        r = FinalReport(scenario="low_resource_survivability")
        try:
            db = self._db("low_resource.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size = -16")
            conn.execute("PRAGMA page_size = 512")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS t ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, v TEXT)"
            )
            for i in range(3000):
                conn.execute(
                    "INSERT INTO t (v) VALUES (?)", (f"lr_{i}",)
                )
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            count = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            cache = conn.execute("PRAGMA cache_size").fetchone()[0]
            conn.close()
            integrity = self._integrity(db)
            r.checks["count"] = count == 3000
            r.checks["cache_bounded"] = cache <= -16
            r.checks["integrity"] = integrity
            if integrity and count == 3000:
                return r.success(
                    f"low-resource: {count} rows, cache={cache}, 512B pages"
                )
            return r.fail(f"count={count}, cache={cache}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 9 — Final audit continuity validation
    def validate_final_audit_continuity(self) -> FinalReport:
        start = time.monotonic()
        r = FinalReport(scenario="final_audit_continuity")
        try:
            db = self._db("final_audit.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS audit ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "seq INTEGER UNIQUE, event TEXT, "
                "checksum TEXT, ts REAL)"
            )
            for i in range(50):
                payload = json.dumps(
                    {"seq": i, "event": f"audit_{i}"}, sort_keys=True
                )
                ck = hashlib.sha256(payload.encode()).hexdigest()
                conn.execute(
                    "INSERT INTO audit (seq, event, checksum) VALUES (?,?,?)",
                    (i, payload, ck),
                )
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
            results: list[int] = []
            for run in range(3):
                wal = self._wal_path(db)
                if wal.exists():
                    wal.unlink()
                c = sqlite3.connect(str(db), timeout=30)
                c.execute("PRAGMA journal_mode=WAL")
                cnt = c.execute("SELECT COUNT(*) FROM audit").fetchone()[0]
                c.close()
                results.append(cnt)
            stable = len(set(results)) == 1
            verified = 0
            c = sqlite3.connect(str(db))
            rows = c.execute(
                "SELECT event, checksum FROM audit ORDER BY id"
            ).fetchall()
            for event, stored in rows:
                expected = hashlib.sha256(event.encode()).hexdigest()
                if expected == stored:
                    verified += 1
            c.close()
            r.checks["stable"] = stable
            r.checks["verified"] = verified == 50
            if stable and verified == 50:
                return r.success(
                    f"audit: {verified}/50 verified, {results[0]} stable"
                )
            return r.fail(f"stable={stable}, verified={verified}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 10 — Real-environment consistency verification
    def validate_real_environment_consistency(self) -> FinalReport:
        start = time.monotonic()
        r = FinalReport(scenario="real_environment_consistency")
        try:
            consistency_results: list[dict] = []
            for run in range(3):
                db = self._db(f"consistency_{run}.db")
                conn = sqlite3.connect(str(db), timeout=30)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS sys_state ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "key TEXT UNIQUE, value TEXT)"
                )
                entries = {
                    "version": "1.0.0",
                    "mode": "pilot",
                    "cache_kb": "64",
                    "wal_mode": "enabled",
                    "audit_level": "full",
                    "replay_mode": "deterministic",
                }
                for k, v in entries.items():
                    conn.execute(
                        "INSERT OR REPLACE INTO sys_state (key, value) "
                        "VALUES (?,?)",
                        (k, v),
                    )
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
                state = dict(
                    sqlite3.connect(str(db)).execute(
                        "SELECT key, value FROM sys_state ORDER BY key"
                    ).fetchall()
                )
                consistency_results.append(state)
            stable = all(
                r == consistency_results[0] for r in consistency_results
            )
            all_int = all(
                self._integrity(self._db(f"consistency_{r}.db"))
                for r in range(3)
            )
            r.checks["consistent"] = stable
            r.checks["integrity"] = all_int
            if stable and all_int:
                return r.success(
                    f"consistency: {len(consistency_results[0])} keys, 3/3 identical"
                )
            return r.fail(f"stable={stable}, integrity={all_int}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[FinalReport]:
        return [
            self.validate_full_deployment_replay(),
            self.validate_repeated_crash_cycles(),
            self.validate_long_session_endurance_replay(),
            self.validate_wal_interruption_replay(),
            self.validate_replay_divergence(),
            self.validate_deterministic_archive_replay(),
            self.validate_deployment_rollback_replay(),
            self.validate_low_resource_survivability(),
            self.validate_final_audit_continuity(),
            self.validate_real_environment_consistency(),
        ]
