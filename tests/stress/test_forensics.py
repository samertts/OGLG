from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.forensics import ForensicsEngine


class TestRuntimeDiagnostics:
    def test_capture_diagnostics(self, tmp_path: Path):
        eng = ForensicsEngine(tmp_path / "forensics")
        report = eng.capture_runtime_diagnostics()
        assert report.passed


class TestAuditSnapshot:
    def test_snapshot_tables(self, tmp_path: Path):
        db = tmp_path / "audit.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.execute("INSERT INTO t VALUES (1)")
        conn.execute("INSERT INTO t VALUES (2)")
        conn.commit()
        conn.close()
        eng = ForensicsEngine(tmp_path / "forensics")
        report = eng.capture_audit_snapshot(db)
        assert report.passed
        assert report.entry_count == 2


class TestReplayMetadata:
    def test_capture_metadata(self, tmp_path: Path):
        db = tmp_path / "replay.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.execute("INSERT INTO t VALUES (1)")
        conn.commit()
        conn.close()
        eng = ForensicsEngine(tmp_path / "forensics")
        report = eng.capture_replay_metadata(db)
        assert report.passed
        assert report.data.get("wal") == "wal"


class TestOperatorTimeline:
    def test_record_actions(self, tmp_path: Path):
        eng = ForensicsEngine(tmp_path / "forensics")
        eng.record_operator_action("op1", "login", "127.0.0.1")
        eng.record_operator_action("op1", "create_draft", "subject=test")
        eng.record_operator_action("op2", "approve", "draft_id=1")
        report = eng.export_operator_timeline()
        assert report.passed
        assert report.entry_count == 3


class TestCrashReconstruction:
    def test_reconstruct_healthy_db(self, tmp_path: Path):
        db = tmp_path / "crash.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.execute("INSERT INTO t VALUES (1)")
        conn.commit()
        conn.close()
        eng = ForensicsEngine(tmp_path / "forensics")
        report = eng.capture_crash_reconstruction(db)
        assert report.passed


class TestWalIncidentDiagnostics:
    def test_diagnose_wal(self, tmp_path: Path):
        db = tmp_path / "wal_incident.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.execute("INSERT INTO t VALUES (1)")
        conn.commit()
        conn.close()
        eng = ForensicsEngine(tmp_path / "forensics")
        report = eng.diagnose_wal_incident(db)
        assert report.passed


class TestSyncIncidentDiagnostics:
    def test_diagnose_sync(self, tmp_path: Path):
        db = tmp_path / "sync_incident.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("CREATE TABLE sync_state (id INTEGER, status TEXT)")
        conn.execute("INSERT INTO sync_state VALUES (1, 'pending')")
        conn.commit()
        conn.close()
        eng = ForensicsEngine(tmp_path / "forensics")
        report = eng.diagnose_sync_incident(db)
        assert report.passed


class TestQueueReplayTrace:
    def test_trace_queue(self, tmp_path: Path):
        db = tmp_path / "queue_trace.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("CREATE TABLE command_queue (id INTEGER, payload TEXT)")
        conn.execute("INSERT INTO command_queue VALUES (1, 'msg1')")
        conn.execute("INSERT INTO command_queue VALUES (2, 'msg2')")
        conn.commit()
        conn.close()
        eng = ForensicsEngine(tmp_path / "forensics")
        report = eng.trace_queue_replay(db)
        assert report.passed


class TestIncidentBundle:
    def test_export_bundle(self, tmp_path: Path):
        db = tmp_path / "bundle.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.execute("INSERT INTO t VALUES (1)")
        conn.execute("INSERT INTO t VALUES (2)")
        conn.commit()
        conn.close()
        eng = ForensicsEngine(tmp_path / "forensics")
        report = eng.export_incident_bundle(db)
        assert report.passed
        assert report.bundle_size_bytes > 0


class TestRunAll:
    def test_all_forensics_operations(self, tmp_path: Path):
        db = tmp_path / "all.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.execute("INSERT INTO t VALUES (1)")
        conn.commit()
        conn.close()
        eng = ForensicsEngine(tmp_path / "forensics")
        assert eng.capture_runtime_diagnostics().passed
        assert eng.capture_audit_snapshot(db).passed
        assert eng.capture_replay_metadata(db).passed
        eng.record_operator_action("op", "test")
        assert eng.export_operator_timeline().passed
        assert eng.capture_crash_reconstruction(db).passed
        assert eng.diagnose_wal_incident(db).passed
        assert eng.diagnose_sync_incident(db).passed
        assert eng.trace_queue_replay(db).passed
        assert eng.export_incident_bundle(db).passed
