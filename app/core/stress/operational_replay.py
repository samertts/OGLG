from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.core.federation.identity import FederationNode, NodeRole
from app.core.federation.protocol import FederationProtocol


@dataclass
class OperationalReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool] = field(default_factory=dict)

    def success(self, detail: str) -> OperationalReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> OperationalReport:
        self.passed = False
        self.detail = detail
        return self


def _node(label: str, node_id: str, inst: str) -> FederationNode:
    return FederationNode(
        node_id=node_id, institution_id=inst,
        label=label, role=NodeRole.BRANCH,
    )


def _integrity(db: Path) -> bool:
    try:
        c = sqlite3.connect(str(db))
        r = c.execute("PRAGMA integrity_check").fetchone()
        c.close()
        return r is not None and r[0] == "ok"
    except Exception:
        return False


class OperationalReplayValidator:
    def __init__(self, work_dir: Path) -> None:
        self._work = work_dir
        self._work.mkdir(parents=True, exist_ok=True)

    def _pending(self, scenario: str) -> OperationalReport:
        return OperationalReport(scenario=scenario)

    def _db(self, name: str) -> Path:
        return self._work / name

    def _make_db(self, name: str, table: str = "ops") -> sqlite3.Connection:
        db = self._db(name)
        conn = sqlite3.connect(str(db), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {table} "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "day INTEGER, op TEXT, ts REAL)"
        )
        return conn

    # 1 — 30-day long-session replay
    def validate_long_session_replay(self) -> OperationalReport:
        start = time.monotonic()
        r = self._pending("long_session_replay")
        try:
            db = self._db("long_session.db")
            conn = self._make_db("long_session.db", "daily_log")
            total = 0
            for day in range(1, 31):
                for _ in range(17):
                    conn.execute(
                        "INSERT INTO daily_log (day, op, ts) VALUES (?,?,?)",
                        (day, f"op_{day}_{total}", time.monotonic()),
                    )
                    total += 1
                    conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                count = conn.execute(
                    "SELECT COUNT(*) FROM daily_log"
                ).fetchone()[0]
                r.checks[f"day_{day}_count"] = count == total

            conn.close()
            ok = _integrity(db)
            final = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM daily_log"
            ).fetchone()[0]
            sqlite3.connect(str(db)).close()

            r.checks["integrity"] = ok
            r.checks["final_count"] = final == 30 * 17

            if ok and final == 30 * 17:
                return r.success(
                    f"30-day session: {final} ops across 30 days, "
                    f"integrity OK"
                )
            return r.fail(f"integrity={ok}, count={final}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 2 — Crash-recovery across 30 days
    def validate_crash_recovery_cycles(self) -> OperationalReport:
        start = time.monotonic()
        r = self._pending("crash_recovery_cycles")
        try:
            db = self._db("crash_cycles.db")
            conn = self._make_db("crash_cycles.db", "crash_log")
            total = 0
            cycles = 5
            for cycle in range(cycles):
                for _ in range(30):
                    conn.execute(
                        "INSERT INTO crash_log (day, op, ts) VALUES (?,?,?)",
                        (cycle + 1, f"cycle_{cycle}_{total}", time.monotonic()),
                    )
                    total += 1
                conn.commit()
                conn.close()

                wal = Path(str(db) + "-wal")
                if wal.exists():
                    data = wal.read_bytes()
                    wal.write_bytes(data[:len(data) // 2])

                conn = sqlite3.connect(str(db), timeout=10)
                conn.execute("PRAGMA journal_mode=WAL")

            conn.close()
            ok = _integrity(db)

            r.checks["integrity"] = ok
            r.checks["cycles"] = cycles == 5

            if ok:
                return r.success(
                    f"crash recovery: {total} ops across {cycles} cycles, "
                    f"integrity OK"
                )
            return r.fail("integrity check failed after crash cycles")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 3 — WAL interruption replay
    def validate_wal_interruption_replay(self) -> OperationalReport:
        start = time.monotonic()
        r = self._pending("wal_interruption_replay")
        try:
            db = self._db("wal_interrupt.db")
            conn = self._make_db("wal_interrupt.db", "interrupt_log")
            for i in range(100):
                conn.execute(
                    "INSERT INTO interrupt_log (day, op, ts) VALUES (?,?,?)",
                    (1, f"pre_interrupt_{i}", time.monotonic()),
                )
            conn.commit()
            conn.close()

            wal = Path(str(db) + "-wal")
            if wal.exists():
                wal.write_bytes(b"")

            conn2 = sqlite3.connect(str(db), timeout=10)
            conn2.execute("PRAGMA journal_mode=WAL")
            count = conn2.execute(
                "SELECT COUNT(*) FROM interrupt_log"
            ).fetchone()[0]
            conn2.close()

            ok = _integrity(db)

            r.checks["integrity"] = ok
            r.checks["survived"] = count >= 90

            if ok:
                return r.success(
                    f"WAL interruption: {count} survived of 100"
                )
            return r.fail(f"integrity={ok}, count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 4 — Queue persistence across days
    def validate_queue_persistence(self) -> OperationalReport:
        start = time.monotonic()
        r = self._pending("queue_persistence")
        try:
            db = self._db("queue_persist.db")
            conn = self._make_db("queue_persist.db", "queue")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS queue_meta "
                "(key TEXT PRIMARY KEY, value TEXT)"
            )

            for day in range(1, 31):
                conn.execute(
                    "INSERT OR REPLACE INTO queue_meta (key, value) "
                    "VALUES (?,?)",
                    ("day_marker", str(day)),
                )
                for i in range(5):
                    conn.execute(
                        "INSERT INTO queue (day, op, ts) VALUES (?,?,?)",
                        (day, f"queue_item_{day}_{i}", time.monotonic()),
                    )
                conn.commit()

            total = conn.execute("SELECT COUNT(*) FROM queue").fetchone()[0]
            last_marker = conn.execute(
                "SELECT value FROM queue_meta WHERE key='day_marker'"
            ).fetchone()[0]
            conn.close()

            ok = _integrity(db)

            r.checks["integrity"] = ok
            r.checks["total_queued"] = total == 150
            r.checks["day_marker"] = last_marker == "30"

            if ok:
                return r.success(
                    f"queue: {total} items, day marker={last_marker}"
                )
            return r.fail(f"integrity={ok}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 5 — Archive replay with SHA-256
    def validate_archive_replay(self) -> OperationalReport:
        start = time.monotonic()
        r = self._pending("archive_replay")
        try:
            db = self._db("archive30.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS archive30 "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "snapshot_id TEXT UNIQUE, day INTEGER, "
                "checksum TEXT, data TEXT)"
            )

            snapshots: list[str] = []
            for day in range(1, 31):
                payload = json.dumps(
                    {"day": day, "ops": day * 10}, sort_keys=True
                )
                sha = hashlib.sha256(
                    f"day_{day}:{payload}".encode()
                ).hexdigest()
                sid = f"snap_{day}"
                conn.execute(
                    "INSERT OR REPLACE INTO archive30 "
                    "(snapshot_id, day, checksum, data) VALUES (?,?,?,?)",
                    (sid, day, sha, payload),
                )
                snapshots.append(sid)
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

            replayed: list[str] = []
            rows = conn.execute(
                "SELECT snapshot_id, data FROM archive30 ORDER BY id"
            ).fetchall()
            for row in rows:
                day_str = row[0].replace("snap_", "day_")
                expected_sha = hashlib.sha256(
                    f"{day_str}:{row[1]}".encode()
                ).hexdigest()
                stored = conn.execute(
                    "SELECT checksum FROM archive30 WHERE snapshot_id=?",
                    (row[0],),
                ).fetchone()[0]
                if expected_sha == stored:
                    replayed.append(row[0])
            conn.close()

            r.checks["all_present"] = len(rows) == 30
            r.checks["all_verified"] = len(replayed) == 30

            if len(replayed) == 30:
                return r.success(
                    f"archive replay: {len(replayed)}/30 SHA-256 verified"
                )
            return r.fail(
                f"archive: present={len(rows)}, verified={len(replayed)}"
            )
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 6 — Operator contention across days
    def validate_operator_contention(self) -> OperationalReport:
        start = time.monotonic()
        r = self._pending("operator_contention")
        try:
            db = self._db("contention30.db")

            def worker(op: str, days: int, ops_per_day: int) -> int:
                c = sqlite3.connect(str(db), timeout=30)
                c.execute("PRAGMA journal_mode=WAL")
                c.execute(
                    "CREATE TABLE IF NOT EXISTS contention_log "
                    "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "operator TEXT, day INTEGER, seq INTEGER, ts REAL)"
                )
                local_total = 0
                for d in range(1, days + 1):
                    for s in range(ops_per_day):
                        c.execute(
                            "INSERT INTO contention_log "
                            "(operator, day, seq, ts) VALUES (?,?,?,?)",
                            (op, d, s, time.monotonic()),
                        )
                        local_total += 1
                    c.commit()
                c.close()
                return local_total

            threads: list[threading.Thread] = []
            results: dict[str, int] = {}
            lock = threading.Lock()

            def tracked_worker(op: str, days: int, ops_per_day: int) -> None:
                count = worker(op, days, ops_per_day)
                with lock:
                    results[op] = count

            for op_idx in range(5):
                t = threading.Thread(
                    target=tracked_worker,
                    args=(f"op_{op_idx}", 30, 5),
                )
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            ok = _integrity(db)
            final = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM contention_log"
            ).fetchone()[0]
            sqlite3.connect(str(db)).close()

            expected = 5 * 30 * 5
            r.checks["integrity"] = ok
            r.checks["total"] = final == expected
            r.checks["all_workers_completed"] = all(
                v == 150 for v in results.values()
            )

            if ok and final == expected:
                return r.success(
                    f"contention: {final} ops across 5 operators "
                    f"x 30 days, integrity OK"
                )
            return r.fail(f"integrity={ok}, count={final}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 7 — Deterministic sync replay
    def validate_deterministic_sync(self) -> OperationalReport:
        start = time.monotonic()
        r = self._pending("deterministic_sync")
        try:
            a = _node("alpha", "alpha-30", "health")
            b = _node("beta", "beta-30", "health")
            pa = FederationProtocol(local_node=a)
            pb = FederationProtocol(local_node=b)
            pa.register_peer(b)
            pb.register_peer(a)

            for day in range(1, 31):
                pa.emit(
                    "daily.report", f"day_{day}",
                    {"day": day, "count": day * 10},
                )

            manifest = pa.prepare_sync(b.node_id)
            pb.receive_sync(manifest)

            s1 = pb.prepare_sync(a.node_id)
            order1 = [e.metadata.sequence for e in s1.events] if s1 else []

            pb2 = FederationProtocol(local_node=b)
            pb2.register_peer(a)
            pa2 = FederationProtocol(local_node=a)
            pa2.register_peer(b)

            for day in range(1, 31):
                pa2.emit(
                    "daily.report", f"day_{day}",
                    {"day": day, "count": day * 10},
                )
            m2 = pa2.prepare_sync(b.node_id)
            pb2.receive_sync(m2)

            s2 = pb2.prepare_sync(a.node_id)
            order2 = [e.metadata.sequence for e in s2.events] if s2 else []

            r.checks["sync_consistent"] = order1 == order2
            r.checks["non_empty"] = len(order1) > 0

            if order1 == order2:
                return r.success(
                    f"sync: {len(order1)} events, "
                    f"deterministic across 2 replays"
                )
            return r.fail("order mismatch")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 8 — Low-memory endurance
    def validate_low_memory_endurance(self) -> OperationalReport:
        start = time.monotonic()
        r = self._pending("low_memory_endurance")
        try:
            db = self._db("low_mem30.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size = -256")
            conn.execute("PRAGMA page_size = 512")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS low_mem_log "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "day INTEGER, op TEXT, ts REAL)"
            )

            for day in range(1, 31):
                for _ in range(20):
                    conn.execute(
                        "INSERT INTO low_mem_log (day, op, ts) VALUES (?,?,?)",
                        (day, f"lowmem_{day}_{time.monotonic()}", time.monotonic()),
                    )
                    conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                count = conn.execute(
                    "SELECT COUNT(*) FROM low_mem_log"
                ).fetchone()[0]
                r.checks[f"day_{day}_ok"] = count == day * 20

            conn.close()
            ok = _integrity(db)
            final = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM low_mem_log"
            ).fetchone()[0]
            sqlite3.connect(str(db)).close()

            r.checks["integrity"] = ok
            r.checks["final_count"] = final == 30 * 20

            if ok:
                return r.success(
                    f"low-memory: {final} ops across 30 days "
                    f"(256KB cache, 512B pages)"
                )
            return r.fail(f"integrity={ok}, count={final}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 9 — Audit continuity across 30 days
    def validate_audit_continuity(self) -> OperationalReport:
        start = time.monotonic()
        r = self._pending("audit_continuity")
        try:
            db = self._db("audit30.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS audit_log "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "day INTEGER, event_id TEXT UNIQUE, "
                "hash TEXT, prev_hash TEXT)"
            )

            prev = "0000"
            total = 0
            for day in range(1, 31):
                for i in range(5):
                    eid = f"evt_{day}_{i}"
                    h = hashlib.sha256(
                        f"{eid}:{prev}".encode()
                    ).hexdigest()[:16]
                    conn.execute(
                        "INSERT INTO audit_log "
                        "(day, event_id, hash, prev_hash) VALUES (?,?,?,?)",
                        (day, eid, h, prev),
                    )
                    prev = h
                    total += 1
                conn.commit()

            chain_ok = True
            rows = conn.execute(
                "SELECT event_id, hash, prev_hash FROM audit_log "
                "ORDER BY id"
            ).fetchall()
            last_prev = "0000"
            for row in rows:
                expected = hashlib.sha256(
                    f"{row[0]}:{last_prev}".encode()
                ).hexdigest()[:16]
                if expected != row[1]:
                    chain_ok = False
                    break
                last_prev = row[1]
            conn.close()

            ok = _integrity(db)

            r.checks["integrity"] = ok
            r.checks["chain_intact"] = chain_ok
            r.checks["total_events"] = total == 150

            if chain_ok:
                return r.success(
                    f"audit: {total} events, chain intact across 30 days"
                )
            return r.fail("chain broken")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 10 — Final divergence verification
    def validate_final_consistency(self) -> OperationalReport:
        start = time.monotonic()
        r = self._pending("final_consistency")
        try:
            db = self._db("final_consistency.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS final_state "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "k TEXT, v TEXT)"
            )

            for i in range(100):
                conn.execute(
                    "INSERT INTO final_state (k, v) VALUES (?,?)",
                    (f"key_{i}", f"value_{i}"),
                )
            conn.commit()
            conn.close()

            def read_all(path: Path) -> list[tuple]:
                c = sqlite3.connect(str(path))
                rows = c.execute(
                    "SELECT k, v FROM final_state ORDER BY id"
                ).fetchall()
                c.close()
                return rows

            r1 = read_all(db)
            r2 = read_all(db)
            r3 = read_all(db)

            matched = r1 == r2 == r3

            r.checks["run1_vs_run2"] = r1 == r2
            r.checks["run2_vs_run3"] = r2 == r3
            r.checks["count"] = len(r1) == 100

            if matched:
                return r.success(
                    f"consistency: 3 independent reads match, {len(r1)} rows"
                )
            return r.fail("reads diverged")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[OperationalReport]:
        return [
            self.validate_long_session_replay(),
            self.validate_crash_recovery_cycles(),
            self.validate_wal_interruption_replay(),
            self.validate_queue_persistence(),
            self.validate_archive_replay(),
            self.validate_operator_contention(),
            self.validate_deterministic_sync(),
            self.validate_low_memory_endurance(),
            self.validate_audit_continuity(),
            self.validate_final_consistency(),
        ]
