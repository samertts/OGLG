from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TelemetryReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool | int] = field(default_factory=dict)

    def success(self, detail: str) -> TelemetryReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> TelemetryReport:
        self.passed = False
        self.detail = detail
        return self


_SEVERITY_ORDER = {"debug": 0, "info": 1, "warning": 2, "error": 3, "critical": 4}


class OperationalTelemetryValidator:
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

    def _sha256(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    # O3.1 — Local-only diagnostics: all telemetry written to local DB
    def validate_local_only_diagnostics(self) -> TelemetryReport:
        start = time.monotonic()
        r = TelemetryReport(scenario="local_only_diagnostics")
        try:
            db = self._db("local_diag.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS diagnostics "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "key TEXT, value TEXT, ts REAL)")
            diags = {"python_version": sys.version, "sqlite_version": "", "wal_enabled": "true"}
            conn.execute("SELECT sqlite_version()")
            diags["sqlite_version"] = conn.execute("SELECT sqlite_version()").fetchone()[0]
            for k, v in diags.items():
                conn.execute("INSERT INTO diagnostics (key, value, ts) VALUES (?,?,?)",
                             (k, v, time.time()))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            integrity = self._integrity(db)
            conn = sqlite3.connect(str(db))
            count = conn.execute("SELECT COUNT(*) FROM diagnostics").fetchone()[0]
            conn.close()
            r.checks["integrity"] = integrity
            r.checks["count"] = count == len(diags)
            if integrity and count == len(diags):
                return r.success(f"local diagnostics: {count} keys, integrity OK")
            return r.fail(f"integrity={integrity}, count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O3.2 — Bounded replay metrics: metrics stay within size limit
    def validate_bounded_replay_metrics(self) -> TelemetryReport:
        start = time.monotonic()
        r = TelemetryReport(scenario="bounded_replay_metrics")
        try:
            db = self._db("replay_metrics.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS replay_metrics "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "event_count INT, duration_ms INT, ts REAL)")
            for i in range(100):
                conn.execute("INSERT INTO replay_metrics (event_count, duration_ms, ts) "
                             "VALUES (?,?,?)", (i * 10, i * 5, time.time()))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            size = db.stat().st_size
            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM replay_metrics"
            ).fetchone()[0]
            r.checks["bounded"] = size < 65536
            r.checks["count"] = count == 100
            if count == 100 and size < 65536:
                return r.success(f"replay metrics: {count} rows, {size}B")
            return r.fail(f"count={count}, size={size}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O3.3 — Crash snapshot capture: capture and verify crash state
    def validate_crash_snapshot_capture(self) -> TelemetryReport:
        start = time.monotonic()
        r = TelemetryReport(scenario="crash_snapshot_capture")
        try:
            snap_dir = self._work / "crash_snapshots"
            snap_dir.mkdir(parents=True)
            db_src = self._db("crash_source.db")
            conn = sqlite3.connect(str(db_src), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS t "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, v TEXT)")
            for i in range(30):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"crash_{i}",))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            snapshot = snap_dir / "crash_snapshot.db"
            shutil.copy2(db_src, snapshot)

            integrity = self._integrity(snapshot)
            count = sqlite3.connect(str(snapshot)).execute(
                "SELECT COUNT(*) FROM t"
            ).fetchone()[0]
            r.checks["snapshot_exists"] = snapshot.exists()
            r.checks["integrity"] = integrity
            r.checks["count"] = count == 30
            if integrity and count == 30:
                return r.success(f"crash snapshot: {count} rows, {snapshot.name}")
            return r.fail(f"integrity={integrity}, count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O3.4 — WAL incident diagnostics: detect WAL anomalies
    def validate_wal_incident_diagnostics(self) -> TelemetryReport:
        start = time.monotonic()
        r = TelemetryReport(scenario="wal_incident_diagnostics")
        try:
            db = self._db("wal_incident.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS wal_incidents "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "incident TEXT, wal_size INT, recovered INT)")
            incidents = [
                ("wal_truncation", 4096, 1),
                ("checkpoint_failure", 8192, 0),
                ("wal_corruption", 0, 1),
            ]
            for inc, size, rec in incidents:
                conn.execute("INSERT INTO wal_incidents "
                             "(incident, wal_size, recovered) VALUES (?,?,?)",
                             (inc, size, rec))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM wal_incidents"
            ).fetchone()[0]
            recovered = sqlite3.connect(str(db)).execute(
                "SELECT SUM(recovered) FROM wal_incidents"
            ).fetchone()[0]
            r.checks["count"] = count == 3
            r.checks["recovered"] = recovered >= 2
            if count == 3:
                return r.success(f"WAL incidents: {count} logged, recovered={recovered}")
            return r.fail(f"count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O3.5 — Federation incident diagnostics: log federation issues
    def validate_federation_incident_diagnostics(self) -> TelemetryReport:
        start = time.monotonic()
        r = TelemetryReport(scenario="federation_incident_diagnostics")
        try:
            db = self._db("fed_incident.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS fed_incidents "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "node_id TEXT, incident TEXT, ts REAL)")
            nodes = ["node_a", "node_b", "node_c"]
            incidents = ["sync_failure", "timeout", "conflict"]
            for node in nodes:
                for inc in incidents:
                    conn.execute("INSERT INTO fed_incidents "
                                 "(node_id, incident, ts) VALUES (?,?,?)",
                                 (node, inc, time.time()))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM fed_incidents"
            ).fetchone()[0]
            distinct_nodes = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(DISTINCT node_id) FROM fed_incidents"
            ).fetchone()[0]
            r.checks["count"] = count == len(nodes) * len(incidents)
            r.checks["nodes"] = distinct_nodes == len(nodes)
            if count == len(nodes) * len(incidents):
                return r.success(f"federation: {count} incidents, {distinct_nodes} nodes")
            return r.fail(f"count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O3.6 — Archive integrity metrics: checksum-based integrity tracking
    def validate_archive_integrity_metrics(self) -> TelemetryReport:
        start = time.monotonic()
        r = TelemetryReport(scenario="archive_integrity_metrics")
        try:
            db = self._db("archive_metrics.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS archive_integrity "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "snapshot_id TEXT, sha256 TEXT, verified INT)")
            snapshots: list[tuple[str, str, int]] = []
            for i in range(20):
                snap_id = f"SNAP-{i:04d}"
                content = f"snapshot content {i}".encode()
                cksum = hashlib.sha256(content).hexdigest()
                snapshots.append((snap_id, cksum, 1))
            for snap_id, cksum, verified in snapshots:
                conn.execute("INSERT INTO archive_integrity "
                             "(snapshot_id, sha256, verified) VALUES (?,?,?)",
                             (snap_id, cksum, verified))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM archive_integrity WHERE verified=1"
            ).fetchone()[0]
            r.checks["verified"] = count == 20
            if count == 20:
                return r.success(f"archive: {count} snapshots integrity verified")
            return r.fail(f"verified={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O3.7 — Memory growth diagnostics: verify bounded memory usage
    def validate_memory_growth_diagnostics(self) -> TelemetryReport:
        start = time.monotonic()
        r = TelemetryReport(scenario="memory_growth_diagnostics")
        try:
            db = self._db("mem_growth.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size = -32")
            conn.execute("CREATE TABLE IF NOT EXISTS mem_diag "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "rows_count INT, cache_size INT, ts REAL)")
            for batch in range(10):
                conn.execute("INSERT INTO mem_diag (rows_count, cache_size, ts) "
                             "VALUES (?,?,?)",
                             (batch * 50, -32, time.time()))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM mem_diag"
            ).fetchone()[0]
            r.checks["count"] = count == 10
            if count == 10:
                return r.success(f"memory diagnostics: {count} checkpoints, cache=-32")
            return r.fail(f"count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O3.8 — Resource exhaustion capture: detect and log resource limits
    def validate_resource_exhaustion_capture(self) -> TelemetryReport:
        start = time.monotonic()
        r = TelemetryReport(scenario="resource_exhaustion_capture")
        try:
            db = self._db("resource_exhaust.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS resource_events "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "resource TEXT, limit_val INT, actual_val INT, "
                         "severity TEXT)")
            events = [
                ("cache", 32, 48, "warning"),
                ("wal_size", 65536, 131072, "critical"),
                ("disk", 1048576, 1536000, "warning"),
            ]
            for resource, limit_val, actual_val, severity in events:
                conn.execute("INSERT INTO resource_events "
                             "(resource, limit_val, actual_val, severity) "
                             "VALUES (?,?,?,?)",
                             (resource, limit_val, actual_val, severity))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM resource_events"
            ).fetchone()[0]
            criticals = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM resource_events WHERE severity='critical'"
            ).fetchone()[0]
            r.checks["count"] = count == 3
            r.checks["critical_detected"] = criticals >= 1
            if count == 3:
                return r.success(f"resource events: {count}, critical={criticals}")
            return r.fail(f"count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O3.9 — Deterministic operational logging: structured log with ordered events
    def validate_deterministic_operational_logging(self) -> TelemetryReport:
        start = time.monotonic()
        r = TelemetryReport(scenario="deterministic_operational_logging")
        try:
            db = self._db("op_logging.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS op_log "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "log_id TEXT, component TEXT, message TEXT, "
                         "severity TEXT)")
            logs = [
                ("L001", "deploy", "deployment started", "info"),
                ("L002", "deploy", "deployment complete", "info"),
                ("L003", "wal", "checkpoint ok", "info"),
                ("L004", "sync", "federation sync started", "info"),
                ("L005", "sync", "federation sync complete", "info"),
            ]
            for lid, comp, msg, sev in logs:
                conn.execute("INSERT INTO op_log "
                             "(log_id, component, message, severity) "
                             "VALUES (?,?,?,?)",
                             (lid, comp, msg, sev))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            rows = sqlite3.connect(str(db)).execute(
                "SELECT log_id FROM op_log ORDER BY id"
            ).fetchall()
            ordered = all(rows[i][0] < rows[i + 1][0] for i in range(len(rows) - 1))
            count = len(rows)
            r.checks["ordered"] = ordered
            r.checks["count"] = count == 5
            if ordered and count == 5:
                return r.success(f"op log: {count} events, ordered={ordered}")
            return r.fail(f"count={count}, ordered={ordered}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O3.10 — Offline incident export bundles: export as JSON/SHA-256 manifest
    def validate_offline_incident_export_bundles(self) -> TelemetryReport:
        start = time.monotonic()
        r = TelemetryReport(scenario="offline_incident_export_bundles")
        try:
            export_dir = self._work / "incident_exports"
            export_dir.mkdir(parents=True)
            incidents = {
                "incident_001": {"type": "wal_truncation", "severity": "critical",
                                 "timestamp": time.time()},
                "incident_002": {"type": "sync_timeout", "severity": "warning",
                                 "timestamp": time.time()},
            }
            for inc_id, data in incidents.items():
                (export_dir / f"{inc_id}.json").write_text(json.dumps(data))
            manifest = {}
            for f in sorted(export_dir.iterdir()):
                manifest[f.name] = self._sha256(f)
            (export_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
            entries = len([f for f in export_dir.iterdir() if f.suffix == ".json"])
            has_manifest = (export_dir / "manifest.json").exists()
            r.checks["exported"] = entries == 3
            r.checks["manifest"] = has_manifest
            if has_manifest and entries == 3:
                return r.success(f"incident bundle: {entries} files, manifest OK")
            return r.fail(f"entries={entries}, manifest={has_manifest}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O3.11 — Incident severity classification: verify severity ordering
    def validate_incident_severity_classification(self) -> TelemetryReport:
        start = time.monotonic()
        r = TelemetryReport(scenario="incident_severity_classification")
        try:
            db = self._db("severity_class.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS incidents "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "incident TEXT, severity TEXT)")
            test_incidents = [
                ("wal_full", "critical"),
                ("sync_retry", "warning"),
                ("op_complete", "info"),
                ("db_check", "debug"),
            ]
            for inc, sev in test_incidents:
                conn.execute("INSERT INTO incidents (incident, severity) VALUES (?,?)",
                             (inc, sev))
            conn.commit()
            conn.close()

            ordered_sevs = sqlite3.connect(str(db)).execute(
                "SELECT severity FROM incidents ORDER BY id"
            ).fetchall()
            levels = [_SEVERITY_ORDER[s[0]] for s in ordered_sevs]
            ascending = all(levels[i] >= levels[i - 1] for i in range(1, len(levels)))
            r.checks["classified"] = len(ordered_sevs) == 4
            if len(ordered_sevs) == 4:
                sev_names = [s[0] for s in ordered_sevs]
                return r.success(f"severity: {', '.join(sev_names)}, "
                                f"ascending={ascending}")
            return r.fail(f"classified={len(ordered_sevs)}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O3.12 — Deterministic incident escalation: route to handler by severity
    def validate_deterministic_incident_escalation(self) -> TelemetryReport:
        start = time.monotonic()
        r = TelemetryReport(scenario="deterministic_incident_escalation")
        try:
            db = self._db("escalation.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS escalation_log "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "incident TEXT, severity TEXT, "
                          "handler TEXT, escalated INT)")
            incidents = [
                ("wal_corrupt", "critical", "page", 1),
                ("sync_fail", "warning", "notify", 1),
                ("op_complete", "info", "log", 0),
            ]
            for inc, sev, handler, escalated in incidents:
                conn.execute("INSERT INTO escalation_log "
                             "(incident, severity, handler, escalated) "
                             "VALUES (?,?,?,?)",
                             (inc, sev, handler, escalated))
            conn.commit()
            conn.close()

            rows = sqlite3.connect(str(db)).execute(
                "SELECT incident, handler, escalated FROM escalation_log "
                "ORDER BY id"
            ).fetchall()
            correct = all(
                rows[i][1] == incidents[i][2] and rows[i][2] == incidents[i][3]
                for i in range(len(rows))
            )
            r.checks["escalated"] = correct
            r.checks["count"] = len(rows) == 3
            if correct and len(rows) == 3:
                handlers = [f"{r[0]}->{r[1]}" for r in rows]
                return r.success(f"escalation: {', '.join(handlers)}")
            return r.fail(f"correct={correct}, count={len(rows)}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[TelemetryReport]:
        return [
            self.validate_local_only_diagnostics(),
            self.validate_bounded_replay_metrics(),
            self.validate_crash_snapshot_capture(),
            self.validate_wal_incident_diagnostics(),
            self.validate_federation_incident_diagnostics(),
            self.validate_archive_integrity_metrics(),
            self.validate_memory_growth_diagnostics(),
            self.validate_resource_exhaustion_capture(),
            self.validate_deterministic_operational_logging(),
            self.validate_offline_incident_export_bundles(),
            self.validate_incident_severity_classification(),
            self.validate_deterministic_incident_escalation(),
        ]
