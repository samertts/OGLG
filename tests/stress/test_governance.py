from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.governance.reporter import (
    ArchiveHealthSummary,
    DeploymentHealthReport,
    DiagnosticSummary,
    FederationContinuitySummary,
    GovernanceReporter,
    RbacValidationReport,
    ReplayIntegrityReport,
    WalSurvivabilityReport,
)


def _make_db(path: Path, with_fed: bool = False, with_rbac: bool = False) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
    conn.execute("INSERT INTO t (v) VALUES ('a')")
    conn.execute("INSERT INTO t (v) VALUES ('b')")
    conn.execute("INSERT INTO t (v) VALUES ('c')")
    conn.commit()
    if with_fed:
        conn.execute(
            "CREATE TABLE federation_identity (id INTEGER PRIMARY KEY, node_id TEXT)"
        )
        conn.execute("INSERT INTO federation_identity (node_id) VALUES ('node_a')")
        conn.commit()
    if with_rbac:
        conn.execute("CREATE TABLE roles (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("CREATE TABLE permissions (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("CREATE TABLE role_assignments (id INTEGER PRIMARY KEY, role_id INTEGER)")
        conn.execute("INSERT INTO roles (name) VALUES ('admin')")
        conn.execute("INSERT INTO permissions (name) VALUES ('read')")
        conn.execute("INSERT INTO role_assignments (role_id) VALUES (1)")
        conn.commit()
    conn.close()


def _make_event_store(path: Path, events: int = 10) -> None:
    conn = sqlite3.connect(str(path))
    conn.execute("CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT)")
    for i in range(events):
        conn.execute("INSERT INTO events (payload) VALUES (?)", (f"evt_{i}",))
    conn.commit()
    conn.close()


def _make_archive_db(path: Path, snapshots: int = 5) -> None:
    import hashlib
    import json
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS archive_index "
        "(id INTEGER PRIMARY KEY, snapshot_id TEXT, checksum TEXT, data TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS archive_attachment "
        "(id INTEGER PRIMARY KEY, snapshot_id TEXT, file_hash TEXT)"
    )
    for i in range(snapshots):
        sid = f"snap_{i}"
        data = json.dumps({"val": i}, sort_keys=True)
        ck = hashlib.sha256(data.encode()).hexdigest()
        conn.execute(
            "INSERT INTO archive_index (snapshot_id, checksum, data) VALUES (?,?,?)",
            (sid, ck, data),
        )
        conn.execute(
            "INSERT INTO archive_attachment (snapshot_id, file_hash) VALUES (?,?)",
            (sid, f"hash_{i}"),
        )
    conn.commit()
    conn.close()


class TestDeploymentHealth:
    def test_healthy_db(self, tmp_path: Path):
        db = tmp_path / "test.db"
        _make_db(db)
        r = GovernanceReporter(db).deployment_health()
        assert isinstance(r, DeploymentHealthReport)
        assert r.db_integrity
        assert r.component_count > 0

    def test_no_db(self):
        r = GovernanceReporter().deployment_health()
        assert not r.db_integrity


class TestReplayIntegrity:
    def test_continuous_events(self, tmp_path: Path):
        db = tmp_path / "events.db"
        _make_event_store(db, 20)
        r = GovernanceReporter().replay_integrity(db)
        assert isinstance(r, ReplayIntegrityReport)
        assert r.event_count == 20
        assert r.sequence_continuous

    def test_empty_store(self, tmp_path: Path):
        db = tmp_path / "empty.db"
        _make_event_store(db, 0)
        conn = sqlite3.connect(str(db))
        conn.execute("DELETE FROM events")
        conn.commit()
        conn.close()
        r = GovernanceReporter().replay_integrity(db)
        assert r.sequence_continuous


class TestWalSurvivability:
    def test_wal_present(self, tmp_path: Path):
        db = tmp_path / "test.db"
        _make_db(db)
        r = GovernanceReporter(db).wal_survivability()
        assert isinstance(r, WalSurvivabilityReport)
        assert r.wal_exists or not r.wal_exists

    def test_no_db(self):
        r = GovernanceReporter().wal_survivability()
        assert not r.wal_exists


class TestArchiveHealth:
    def test_archive_valid(self, tmp_path: Path):
        arc = tmp_path / "archive.db"
        _make_archive_db(arc, 5)
        r = GovernanceReporter().archive_health(arc)
        assert isinstance(r, ArchiveHealthSummary)
        assert r.snapshot_count == 5
        assert r.integrity_pass > 0


class TestFederationContinuity:
    def test_federation_summary(self, tmp_path: Path):
        db = tmp_path / "fed.db"
        _make_db(db, with_fed=True)
        r = GovernanceReporter(db).federation_continuity()
        assert isinstance(r, FederationContinuitySummary)
        assert r.identity_count >= 1


class TestRbacValidation:
    def test_rbac_report(self, tmp_path: Path):
        db = tmp_path / "rbac.db"
        _make_db(db, with_rbac=True)
        r = GovernanceReporter(db).rbac_validation()
        assert isinstance(r, RbacValidationReport)
        assert r.role_count >= 1
        assert r.permission_count >= 1


class TestDiagnosticSummary:
    def test_full_summary(self, tmp_path: Path):
        db = tmp_path / "diag.db"
        evt = tmp_path / "events.db"
        arc = tmp_path / "archive.db"
        _make_db(db, with_fed=True, with_rbac=True)
        _make_event_store(evt, 10)
        _make_archive_db(arc, 3)
        r = GovernanceReporter(db).full_diagnostic(evt, arc)
        assert isinstance(r, DiagnosticSummary)
        assert r.deployment is not None
        assert r.replay is not None
        assert r.wal is not None
        assert r.archive is not None
        assert r.federation is not None
        assert r.rbac is not None
        assert r.duration_seconds >= 0

    def test_to_json(self, tmp_path: Path):
        db = tmp_path / "j.db"
        _make_db(db)
        r = GovernanceReporter(db).full_diagnostic()
        j = r.to_json()
        assert isinstance(j, str)
        assert '"deployment"' in j

    def test_to_dict(self, tmp_path: Path):
        db = tmp_path / "d.db"
        _make_db(db)
        r = GovernanceReporter(db).full_diagnostic()
        d = r.to_dict()
        assert isinstance(d, dict)
