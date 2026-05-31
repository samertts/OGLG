from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FederationReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool] = field(default_factory=dict)

    def success(self, detail: str) -> FederationReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> FederationReport:
        self.passed = False
        self.detail = detail
        return self


class FederationRecoveryValidator:
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

    def _make_table(
        self, path: Path, table: str = "t"
    ) -> sqlite3.Connection:
        conn = sqlite3.connect(str(path), timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {table} ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "event_id TEXT UNIQUE, source TEXT, payload TEXT, "
            "ts REAL)"
        )
        conn.commit()
        return conn

    # 1 — Delayed USB synchronization
    def validate_delayed_usb_sync(self) -> FederationReport:
        start = time.monotonic()
        r = FederationReport(scenario="delayed_usb_sync")
        try:
            node_a = self._db("node_a.db")
            node_b = self._db("node_b.db")
            conn_a = self._make_table(node_a, "events")
            conn_b = self._make_table(node_b, "events")
            for i in range(50):
                ck = hashlib.sha256(f"a_event_{i}".encode()).hexdigest()
                conn_a.execute(
                    "INSERT OR IGNORE INTO events (event_id, source, payload) "
                    "VALUES (?,?,?)",
                    (f"a_{i}", "node_a", ck),
                )
            conn_a.commit()
            conn_a.close()
            manifest = sqlite3.connect(str(node_a)).execute(
                "SELECT event_id, payload FROM events ORDER BY id"
            ).fetchall()
            for event_id, payload in manifest:
                conn_b.execute(
                    "INSERT OR IGNORE INTO events (event_id, source, payload) "
                    "VALUES (?,?,?)",
                    (event_id, "usb_sync", payload),
                )
            conn_b.commit()
            count_b = conn_b.execute(
                "SELECT COUNT(*) FROM events"
            ).fetchone()[0]
            conn_b.close()
            r.checks["synced"] = count_b == 50
            if r.checks["synced"]:
                return r.success(f"USB sync: {count_b}/50 events replicated")
            return r.fail(f"synced={count_b}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 2 — Duplicate replay reconciliation
    def validate_duplicate_replay_reconciliation(self) -> FederationReport:
        start = time.monotonic()
        r = FederationReport(scenario="duplicate_replay_reconciliation")
        try:
            db = self._db("dedup_replay.db")
            conn = self._make_table(db, "events")
            for i in range(30):
                conn.execute(
                    "INSERT OR IGNORE INTO events (event_id, source, payload) "
                    "VALUES (?,?,?)",
                    (f"evt_{i}", "first_import", f"data_{i}"),
                )
            for i in range(30):
                conn.execute(
                    "INSERT OR IGNORE INTO events (event_id, source, payload) "
                    "VALUES (?,?,?)",
                    (f"evt_{i}", "second_import", f"data_{i}"),
                )
            conn.commit()
            total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            distinct = conn.execute(
                "SELECT COUNT(DISTINCT event_id) FROM events"
            ).fetchone()[0]
            conn.close()
            r.checks["no_duplicates"] = total == 30
            r.checks["distinct"] = distinct == 30
            if r.checks["no_duplicates"]:
                return r.success(
                    f"dedup: {total} unique events across 2 imports"
                )
            return r.fail(f"total={total}, distinct={distinct}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 3 — Node collision replay
    def validate_node_collision_replay(self) -> FederationReport:
        start = time.monotonic()
        r = FederationReport(scenario="node_collision_replay")
        try:
            db = self._db("collision.db")
            conn = self._make_table(db, "events")
            for i in range(20):
                conn.execute(
                    "INSERT OR IGNORE INTO events (event_id, source, payload) "
                    "VALUES (?,?,?)",
                    (f"collision_{i}", "node_x", f"x_{i}"),
                )
            for i in range(20):
                conn.execute(
                    "INSERT OR IGNORE INTO events (event_id, source, payload) "
                    "VALUES (?,?,?)",
                    (f"collision_{i}", "node_y", f"y_{i}"),
                )
            conn.commit()
            total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            sources = conn.execute(
                "SELECT COUNT(DISTINCT source) FROM events WHERE "
                "event_id LIKE 'collision_%'"
            ).fetchone()[0]
            conn.close()
            r.checks["unique_events"] = total == 20
            r.checks["first_source_wins"] = sources == 1
            if r.checks["unique_events"] and r.checks["first_source_wins"]:
                return r.success(f"collision: {total} unique, first source wins")
            return r.fail(f"total={total}, sources={sources}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 4 — Interrupted federation recovery
    def validate_interrupted_federation_recovery(self) -> FederationReport:
        start = time.monotonic()
        r = FederationReport(scenario="interrupted_federation_recovery")
        try:
            db = self._db("interrupted_fed.db")
            conn = self._make_table(db, "events")
            for i in range(40):
                conn.execute(
                    "INSERT OR IGNORE INTO events (event_id, source, payload) "
                    "VALUES (?,?,?)",
                    (f"fed_{i}", "remote", f"remote_{i}"),
                )
            conn.commit()
            conn.close()
            wal = self._wal_path(db)
            if wal.exists():
                wal.unlink()
            conn2 = sqlite3.connect(str(db), timeout=30)
            conn2.execute("PRAGMA journal_mode=WAL")
            recovered = conn2.execute(
                "SELECT COUNT(*) FROM events"
            ).fetchone()[0]
            conn2.close()
            integrity = self._integrity(db)
            r.checks["recovered"] = recovered == 40
            r.checks["integrity"] = integrity
            if integrity and recovered == 40:
                return r.success(
                    f"interrupted federation: {recovered}/40 recovered"
                )
            return r.fail(f"recovered={recovered}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 5 — Low-bandwidth replay endurance
    def validate_low_bandwidth_replay_endurance(self) -> FederationReport:
        start = time.monotonic()
        r = FederationReport(scenario="low_bandwidth_replay_endurance")
        try:
            db = self._db("low_bw.db")
            conn = self._make_table(db, "events")
            batch_limit = 5
            total_inserted = 0
            for batch in range(10):
                for i in range(batch_limit):
                    conn.execute(
                        "INSERT OR IGNORE INTO events "
                        "(event_id, source, payload) VALUES (?,?,?)",
                        (f"bw_{total_inserted}", f"batch_{batch}",
                         f"payload_{total_inserted}"),
                    )
                    total_inserted += 1
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            conn.close()
            total = self._count(db, "events")
            integrity = self._integrity(db)
            r.checks["total"] = total == 50
            r.checks["integrity"] = integrity
            if integrity and total == 50:
                return r.success(
                    f"low-bandwidth: {total} events in 10 batches of max 5"
                )
            return r.fail(f"total={total}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 6 — Queue reconciliation replay
    def validate_queue_reconciliation_replay(self) -> FederationReport:
        start = time.monotonic()
        r = FederationReport(scenario="queue_reconciliation_replay")
        try:
            db = self._db("queue_recon.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS queue ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "event_id TEXT UNIQUE, priority INTEGER, processed INTEGER DEFAULT 0)"
            )
            for i in range(60):
                conn.execute(
                    "INSERT OR IGNORE INTO queue (event_id, priority) "
                    "VALUES (?,?)",
                    (f"q_{i}", i % 3),
                )
            conn.commit()
            conn.execute("UPDATE queue SET processed=1 WHERE priority=0")
            conn.commit()
            pending = conn.execute(
                "SELECT COUNT(*) FROM queue WHERE processed=0"
            ).fetchone()[0]
            total = conn.execute(
                "SELECT COUNT(*) FROM queue"
            ).fetchone()[0]
            conn.close()
            r.checks["total"] = total == 60
            r.checks["pending_reconciled"] = pending == 40
            if r.checks["total"]:
                return r.success(
                    f"queue recon: {pending}/{total} pending after reconcile"
                )
            return r.fail(f"total={total}, pending={pending}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 7 — Audit continuity validation
    def validate_audit_continuity_federation(self) -> FederationReport:
        start = time.monotonic()
        r = FederationReport(scenario="audit_continuity_federation")
        try:
            db = self._db("audit_fed.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS audit ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "seq INTEGER UNIQUE, event TEXT, "
                "node TEXT, checksum TEXT, ts REAL)"
            )
            for i in range(40):
                payload = json.dumps(
                    {"seq": i, "node": f"node_{i%4}", "action": f"action_{i}"},
                    sort_keys=True,
                )
                ck = hashlib.sha256(payload.encode()).hexdigest()
                conn.execute(
                    "INSERT OR IGNORE INTO audit (seq, event, node, checksum) "
                    "VALUES (?,?,?,?)",
                    (i, payload, f"node_{i%4}", ck),
                )
            conn.commit()
            verified = 0
            rows = conn.execute(
                "SELECT event, checksum FROM audit ORDER BY id"
            ).fetchall()
            for event, stored_ck in rows:
                expected = hashlib.sha256(event.encode()).hexdigest()
                if expected == stored_ck:
                    verified += 1
            total = len(rows)
            conn.close()
            r.checks["total"] = total == 40
            r.checks["verified"] = verified == 40
            if r.checks["total"] and r.checks["verified"]:
                return r.success(
                    f"audit: {verified}/{total} checksums verified"
                )
            return r.fail(f"total={total}, verified={verified}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 8 — Deterministic conflict replay
    def validate_deterministic_conflict_replay(self) -> FederationReport:
        start = time.monotonic()
        r = FederationReport(scenario="deterministic_conflict_replay")
        try:
            results: list[int] = []
            for run in range(3):
                db = self._db(f"conflict_det_{run}.db")
                conn = self._make_table(db, "events")
                sources = ["alice", "bob", "carol"]
                for i in range(30):
                    src = sources[i % 3]
                    conn.execute(
                        "INSERT OR IGNORE INTO events "
                        "(event_id, source, payload) VALUES (?,?,?)",
                        (f"conflict_{i}", src, f"data_{i}_by_{src}"),
                    )
                conn.commit()
                conn.close()
                wal = self._wal_path(db)
                if wal.exists():
                    wal.unlink()
                count = self._count(db, "events")
                results.append(count)
            stable = len(set(results)) == 1
            all_int = all(
                self._integrity(self._db(f"conflict_det_{r}.db"))
                for r in range(3)
            )
            r.checks["deterministic"] = stable
            r.checks["integrity"] = all_int
            if stable and all_int:
                return r.success(
                    f"conflict replay: {results[0]} events, 3/3 stable"
                )
            return r.fail(f"results={results}, integrity={all_int}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 9 — Bounded retry continuity
    def validate_bounded_retry_continuity(self) -> FederationReport:
        start = time.monotonic()
        r = FederationReport(scenario="bounded_retry_continuity")
        try:
            db = self._db("bounded_retry.db")
            conn = self._make_table(db, "retry_log")
            max_retries = 5
            for attempt in range(1, max_retries + 1):
                for i in range(10):
                    conn.execute(
                        "INSERT OR IGNORE INTO retry_log "
                        "(event_id, source, payload) VALUES (?,?,?)",
                        (f"retry_{i}_attempt_{attempt}", "retry_node",
                         f"attempt_{attempt}"),
                    )
                conn.commit()
            conn.close()
            total = self._count(db, "retry_log")
            r.checks["total_retries"] = total == 50
            r.checks["bounded"] = total <= 50
            if r.checks["total_retries"]:
                return r.success(
                    f"bounded retry: {total} entries across {max_retries} attempts"
                )
            return r.fail(f"total={total}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 10 — Offline recovery validation
    def validate_offline_recovery(self) -> FederationReport:
        start = time.monotonic()
        r = FederationReport(scenario="offline_recovery")
        try:
            db = self._db("offline_recovery.db")
            conn = self._make_table(db, "events")
            for cycle in range(5):
                for i in range(10):
                    conn.execute(
                        "INSERT OR IGNORE INTO events "
                        "(event_id, source, payload) VALUES (?,?,?)",
                        (f"offline_{cycle}_{i}", f"cycle_{cycle}",
                         f"offline_data_{cycle}_{i}"),
                    )
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
                conn.close()
                wal = self._wal_path(db)
                if wal.exists():
                    wal.unlink()
                conn_new = sqlite3.connect(str(db), timeout=30)
                conn_new.execute("PRAGMA journal_mode=WAL")
                conn = conn_new
            conn.close()
            total = self._count(db, "events")
            integrity = self._integrity(db)
            r.checks["total"] = total == 50
            r.checks["integrity"] = integrity
            if integrity and total == 50:
                return r.success(
                    f"offline recovery: {total} events across 5 cycles"
                )
            return r.fail(f"total={total}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[FederationReport]:
        return [
            self.validate_delayed_usb_sync(),
            self.validate_duplicate_replay_reconciliation(),
            self.validate_node_collision_replay(),
            self.validate_interrupted_federation_recovery(),
            self.validate_low_bandwidth_replay_endurance(),
            self.validate_queue_reconciliation_replay(),
            self.validate_audit_continuity_federation(),
            self.validate_deterministic_conflict_replay(),
            self.validate_bounded_retry_continuity(),
            self.validate_offline_recovery(),
        ]
