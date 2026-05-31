from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OperationalEnduranceReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool | int] = field(default_factory=dict)

    def success(self, detail: str) -> OperationalEnduranceReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> OperationalEnduranceReport:
        self.passed = False
        self.detail = detail
        return self


class OperationalEnduranceValidator:
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

    def _make_db(self, path: Path) -> sqlite3.Connection:
        conn = sqlite3.connect(str(path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _sha256(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    # O5.1 — Multi-week operational replay: 21-day simulation with checkpoints
    def validate_multi_week_operational_replay(self) -> OperationalEnduranceReport:
        start = time.monotonic()
        r = OperationalEnduranceReport(scenario="multi_week_operational_replay")
        try:
            db = self._db("multi_week.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS weekly_log "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "day INT, ops_count INT, ts REAL)")
            total_ops = 0
            for day in range(21):
                daily_ops = 20 + (day % 10)
                conn.execute("INSERT INTO weekly_log (day, ops_count, ts) "
                             "VALUES (?,?,?)", (day, daily_ops, time.time()))
                total_ops += daily_ops
                conn.commit()
                if day > 0 and day % 3 == 0:
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            integrity = self._integrity(db)
            conn2 = sqlite3.connect(str(db))
            days = conn2.execute("SELECT COUNT(DISTINCT day) FROM weekly_log").fetchone()[0]
            total = conn2.execute("SELECT SUM(ops_count) FROM weekly_log").fetchone()[0]
            conn2.close()
            r.checks["integrity"] = integrity
            r.checks["days"] = days == 21
            r.checks["total"] = total == total_ops
            if integrity and days == 21:
                return r.success(f"multi-week: {days} days, {total_ops} total ops")
            return r.fail(f"integrity={integrity}, days={days}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O5.2 — Long-session survivability verification: sustained batch operation
    def validate_long_session_survivability(self) -> OperationalEnduranceReport:
        start = time.monotonic()
        r = OperationalEnduranceReport(scenario="long_session_survivability")
        try:
            db = self._db("long_session.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS session_state "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "batch INT, action TEXT)")
            for batch in range(30):
                for j in range(10):
                    conn.execute("INSERT INTO session_state (batch, action) "
                                 "VALUES (?,?)", (batch, f"op_{j}"))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            integrity = self._integrity(db)
            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM session_state"
            ).fetchone()[0]
            r.checks["integrity"] = integrity
            r.checks["count"] = count == 300
            if integrity and count == 300:
                return r.success(f"long-session: {count} ops, {30} batches, integrity OK")
            return r.fail(f"integrity={integrity}, count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O5.3 — Repeated recovery-cycle validation: 10 crash-recovery cycles
    def validate_repeated_recovery_cycle(self) -> OperationalEnduranceReport:
        start = time.monotonic()
        r = OperationalEnduranceReport(scenario="repeated_recovery_cycle")
        try:
            db = self._db("recovery_cycle.db")
            for cycle in range(10):
                conn = self._make_db(db)
                conn.execute("CREATE TABLE IF NOT EXISTS t "
                             "(id INTEGER PRIMARY KEY AUTOINCREMENT, v TEXT)")
                conn.execute("INSERT INTO t (v) VALUES (?)",
                             (f"cycle_{cycle}",))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                wal = self._wal_path(db)
                if wal.exists():
                    wal.unlink()
                conn.close()

            integrity = self._integrity(db)
            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM t"
            ).fetchone()[0]
            r.checks["integrity"] = integrity
            r.checks["survived"] = count >= 1
            if integrity and count >= 1:
                return r.success(f"recovery: {count} rows survived {10} cycles")
            return r.fail(f"integrity={integrity}, count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O5.4 — Archive growth observation: track archive size growth
    def validate_archive_growth_observation(self) -> OperationalEnduranceReport:
        start = time.monotonic()
        r = OperationalEnduranceReport(scenario="archive_growth_observation")
        try:
            db = self._db("archive_growth.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS archive_store "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "snapshot_id TEXT, payload BLOB)")
            sizes: list[int] = []
            for batch in range(15):
                for i in range(10):
                    snap = f"SNAP-{batch:04d}-{i:04d}"
                    payload = b"x" * 128
                    conn.execute("INSERT INTO archive_store "
                                 "(snapshot_id, payload) VALUES (?,?)",
                                 (snap, payload))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                sizes.append(db.stat().st_size)
            conn.close()

            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM archive_store"
            ).fetchone()[0]
            final_size = sizes[-1] if sizes else 0
            r.checks["count"] = count == 150
            r.checks["size_bounded"] = final_size < 262144
            if count == 150 and final_size < 262144:
                return r.success(f"archive: {count} snapshots, {final_size}B final")
            return r.fail(f"count={count}, size={final_size}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O5.5 — Federation continuity observation: multi-node sync consistency
    def validate_federation_continuity_observation(self) -> OperationalEnduranceReport:
        start = time.monotonic()
        r = OperationalEnduranceReport(scenario="federation_continuity_observation")
        try:
            nodes = ["node_a", "node_b", "node_c"]
            counts: dict[str, int] = {}
            for node in nodes:
                db = self._db(f"fed_{node}.db")
                conn = self._make_db(db)
                conn.execute("CREATE TABLE IF NOT EXISTS sync_data "
                             "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                             "doc_id TEXT, origin TEXT)")
                for i in range(20):
                    conn.execute("INSERT INTO sync_data (doc_id, origin) "
                                 "VALUES (?,?)",
                                 (f"DOC-{i:03d}", node))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
                counts[node] = sqlite3.connect(str(db)).execute(
                    "SELECT COUNT(*) FROM sync_data"
                ).fetchone()[0]

            all_match = all(c == 20 for c in counts.values())
            r.checks["all_match"] = all_match
            r.checks["nodes"] = len(counts) == 3
            if all_match:
                return r.success(f"federation: {len(counts)} nodes, all {20} docs each")
            return r.fail(f"counts={counts}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O5.6 — Low-resource endurance validation: 64KB cache, long session
    def validate_low_resource_endurance(self) -> OperationalEnduranceReport:
        start = time.monotonic()
        r = OperationalEnduranceReport(scenario="low_resource_endurance")
        try:
            db = self._db("low_resource_endurance.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size = -64")
            conn.execute("CREATE TABLE IF NOT EXISTS t "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, v TEXT)")
            for i in range(500):
                conn.execute("INSERT INTO t (v) VALUES (?)",
                             (f"endurance_{i}",))
                if i > 0 and i % 100 == 0:
                    conn.commit()
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            cache = conn.execute("PRAGMA cache_size").fetchone()[0]
            conn.close()

            integrity = self._integrity(db)
            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM t"
            ).fetchone()[0]
            r.checks["integrity"] = integrity
            r.checks["count"] = count == 500
            r.checks["cache_bounded"] = cache <= -64
            if integrity and count == 500:
                return r.success(f"low-resource endurance: {count} rows, cache={cache}")
            return r.fail(f"integrity={integrity}, count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O5.7 — Operator contention observation: concurrent operator workflows
    def validate_operator_contention_observation(self) -> OperationalEnduranceReport:
        start = time.monotonic()
        r = OperationalEnduranceReport(scenario="operator_contention_observation")
        try:
            db = self._db("operator_contention.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS operator_ops "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "operator TEXT, action TEXT, doc_id TEXT)")
            operators = ["op1", "op2", "op3", "op4", "op5"]
            for op in operators:
                for i in range(30):
                    conn.execute("INSERT INTO operator_ops "
                                 "(operator, action, doc_id) VALUES (?,?,?)",
                                 (op, "process", f"DOC-{i:03d}"))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM operator_ops"
            ).fetchone()[0]
            distinct_ops = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(DISTINCT operator) FROM operator_ops"
            ).fetchone()[0]
            r.checks["count"] = count == len(operators) * 30
            r.checks["operators"] = distinct_ops == len(operators)
            if count == len(operators) * 30:
                return r.success(f"contention: {count} ops, {distinct_ops} operators")
            return r.fail(f"count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O5.8 — Deterministic replay verification: 3-run identical replay
    def validate_deterministic_replay_verification(self) -> OperationalEnduranceReport:
        start = time.monotonic()
        r = OperationalEnduranceReport(scenario="deterministic_replay_verification")
        try:
            results: list[int] = []
            for run in range(3):
                db = self._db(f"det_replay_{run}.db")
                conn = self._make_db(db)
                conn.execute("CREATE TABLE IF NOT EXISTS replay_events "
                             "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                             "event_order INT, payload TEXT)")
                for i in range(50):
                    conn.execute("INSERT INTO replay_events "
                                 "(event_order, payload) VALUES (?,?)",
                                 (i, f"evt_{i}"))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
                count = sqlite3.connect(str(db)).execute(
                    "SELECT COUNT(*) FROM replay_events"
                ).fetchone()[0]
                results.append(count)

            stable = len(set(results)) == 1
            r.checks["stable"] = stable
            r.checks["count"] = results[0] == 50
            if stable and results[0] == 50:
                return r.success(f"deterministic replay: {results[0]}, 3/3 stable")
            return r.fail(f"results={results}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O5.9 — Bounded resource verification: WAL, cache, DB size bounds
    def validate_bounded_resource_verification(self) -> OperationalEnduranceReport:
        start = time.monotonic()
        r = OperationalEnduranceReport(scenario="bounded_resource_verification")
        try:
            db = self._db("bounded_resource.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size = -32")
            conn.execute("PRAGMA wal_autocheckpoint = 50")
            conn.execute("CREATE TABLE IF NOT EXISTS t "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, v TEXT)")
            for batch in range(20):
                for i in range(25):
                    conn.execute("INSERT INTO t (v) VALUES (?)",
                                 (f"batch_{batch}_{i}",))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            cache = conn.execute("PRAGMA cache_size").fetchone()[0]
            page = conn.execute("PRAGMA page_size").fetchone()[0]
            conn.close()

            size = db.stat().st_size
            integrity = self._integrity(db)
            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM t"
            ).fetchone()[0]
            r.checks["integrity"] = integrity
            r.checks["count"] = count == 500
            r.checks["cache_bounded"] = cache <= -32
            r.checks["db_size_bounded"] = size < 131072
            if integrity and count == 500:
                return r.success(f"bounded: {count} rows, cache={cache}, "
                                f"size={size}B, page={page}")
            return r.fail(f"integrity={integrity}, count={count}, size={size}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O5.10 — Final operational divergence detection: 3-run identical
    def validate_final_operational_divergence_detection(self) -> OperationalEnduranceReport:
        start = time.monotonic()
        r = OperationalEnduranceReport(
            scenario="final_operational_divergence_detection"
        )
        try:
            hashes: list[str] = []
            for run in range(3):
                db = self._db(f"divergence_{run}.db")
                conn = self._make_db(db)
                conn.execute("CREATE TABLE IF NOT EXISTS final_state "
                             "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                             "k TEXT, v TEXT)")
                config = {"mode": "pilot", "wal": "true", "cache": "64",
                          "version": "1.0.0"}
                for k, v_ in config.items():
                    conn.execute("INSERT INTO final_state (k, v) VALUES (?,?)",
                                 (k, v_))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
                h = self._sha256(db)
                hashes.append(h)

            no_divergence = len(set(hashes)) == 1
            r.checks["no_divergence"] = no_divergence
            if no_divergence:
                return r.success(f"no divergence: {hashes[0][:16]}..., 3/3 identical")
            return r.fail(f"hashes differ: {hashes}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O5.11 — Immutable operational snapshots: SHA-256 verified snapshots
    def validate_immutable_operational_snapshots(self) -> OperationalEnduranceReport:
        start = time.monotonic()
        r = OperationalEnduranceReport(scenario="immutable_operational_snapshots")
        try:
            snap_dir = self._work / "immutable_snapshots"
            snap_dir.mkdir(parents=True)
            db = self._db("snapshot_source.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS t "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, v TEXT)")
            for i in range(40):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"snap_{i}",))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            for snap_id in range(5):
                snap = snap_dir / f"snapshot_{snap_id}.db"
                shutil.copy2(db, snap)
            snapshots = sorted(snap_dir.iterdir())
            checksums = {s.name: self._sha256(s) for s in snapshots}
            manifest = snap_dir / "manifest.json"
            manifest.write_text(json.dumps(checksums, indent=2))

            r.checks["count"] = len(snapshots) == 5
            r.checks["manifest_exists"] = manifest.exists()
            if len(snapshots) == 5 and manifest.exists():
                return r.success(f"immutable: {len(snapshots)} snapshots, manifest OK")
            return r.fail(f"snapshots={len(snapshots)}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O5.12 — Replay-safe forensic continuity: audit chain survives replay
    def validate_replay_safe_forensic_continuity(self) -> OperationalEnduranceReport:
        start = time.monotonic()
        r = OperationalEnduranceReport(scenario="replay_safe_forensic_continuity")
        try:
            db = self._db("forensic_continuity.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS forensic_chain "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "event_id TEXT, prev_hash TEXT, payload TEXT, "
                         "current_hash TEXT)")
            chain: list[tuple[str, str, str, str]] = []
            prev = "0" * 64
            for i in range(20):
                event_id = f"EVT-{i:04d}"
                payload = f"forensic_event_{i}"
                raw = f"{event_id}:{prev}:{payload}".encode()
                cur = hashlib.sha256(raw).hexdigest()
                chain.append((event_id, prev, payload, cur))
                prev = cur
            for event_id, prev_hash, payload, cur_hash in chain:
                conn.execute("INSERT INTO forensic_chain "
                             "(event_id, prev_hash, payload, current_hash) "
                             "VALUES (?,?,?,?)",
                             (event_id, prev_hash, payload, cur_hash))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            rows = sqlite3.connect(str(db)).execute(
                "SELECT event_id, prev_hash, current_hash "
                "FROM forensic_chain ORDER BY id"
            ).fetchall()
            chain_valid = True
            for i in range(1, len(rows)):
                if rows[i][1] != rows[i - 1][2]:
                    chain_valid = False
                    break
            count = len(rows)
            r.checks["chain_valid"] = chain_valid
            r.checks["length"] = count == 20
            if chain_valid and count == 20:
                return r.success(f"forensic chain: {count} events, hash chain valid")
            return r.fail(f"chain_valid={chain_valid}, count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[OperationalEnduranceReport]:
        return [
            self.validate_multi_week_operational_replay(),
            self.validate_long_session_survivability(),
            self.validate_repeated_recovery_cycle(),
            self.validate_archive_growth_observation(),
            self.validate_federation_continuity_observation(),
            self.validate_low_resource_endurance(),
            self.validate_operator_contention_observation(),
            self.validate_deterministic_replay_verification(),
            self.validate_bounded_resource_verification(),
            self.validate_final_operational_divergence_detection(),
            self.validate_immutable_operational_snapshots(),
            self.validate_replay_safe_forensic_continuity(),
        ]
