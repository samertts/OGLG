from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ReadinessReport:
    scenario: str
    passed: bool
    duration_seconds: float = 0.0
    detail: str = ""


class GovernmentReadinessValidator:
    def __init__(self, workspace: Path) -> None:
        self._workspace = workspace
        self._workspace.mkdir(parents=True, exist_ok=True)

    def _db(self, name: str) -> Path:
        return self._workspace / name

    def _seed_wal_db(self, db: Path, tables: list[str]) -> sqlite3.Connection:
        conn = sqlite3.connect(str(db), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        for t in tables:
            conn.execute(f"CREATE TABLE IF NOT EXISTS {t} (id INTEGER, val TEXT)")
        return conn

    def validate_ministry_workflow(self) -> ReadinessReport:
        start = time.monotonic()
        db = self._db("ministry.db")
        conn = self._seed_wal_db(db, ["drafts", "approvals", "archive", "print_jobs"])
        for i in range(100):
            conn.execute("INSERT INTO drafts VALUES (?, ?)", (i, f"draft_{i}"))
            conn.execute("INSERT INTO approvals VALUES (?, ?)", (i, "pending"))
        conn.commit()
        for i in range(100):
            conn.execute("UPDATE approvals SET val='approved' WHERE id=?", (i,))
            conn.execute("INSERT INTO archive VALUES (?, ?)", (i, f"archived_{i}"))
            if i < 50:
                conn.execute("INSERT INTO print_jobs VALUES (?, ?)", (i, "queued"))
        conn.commit()
        draft_count = conn.execute("SELECT COUNT(*) FROM drafts").fetchone()[0]
        approval_count = conn.execute(
            "SELECT COUNT(*) FROM approvals WHERE val='approved'"
        ).fetchone()[0]
        archive_count = conn.execute("SELECT COUNT(*) FROM archive").fetchone()[0]
        conn.close()
        ok = draft_count == 100 and approval_count == 100 and archive_count == 100
        return ReadinessReport(
            "ministry_workflow", ok, time.monotonic() - start,
            f"drafts={draft_count}, approved={approval_count}, archived={archive_count}",
        )

    def validate_archive_department(self) -> ReadinessReport:
        start = time.monotonic()
        db = self._db("archive_dept.db")
        conn = self._seed_wal_db(db, ["archive_index", "attachments"])
        for i in range(500):
            conn.execute("INSERT INTO archive_index VALUES (?, ?)", (i, f"doc_{i}"))
            conn.execute("INSERT INTO attachments VALUES (?, ?)", (i, f"att_{i}"))
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        index_count = conn.execute("SELECT COUNT(*) FROM archive_index").fetchone()[0]
        att_count = conn.execute("SELECT COUNT(*) FROM attachments").fetchone()[0]
        conn.execute("DELETE FROM archive_index WHERE id % 2 = 0")
        conn.commit()
        after_delete = conn.execute("SELECT COUNT(*) FROM archive_index").fetchone()[0]
        conn.execute("VACUUM")
        conn.close()
        ok = index_count == 500 and att_count == 500 and after_delete == 250
        return ReadinessReport(
            "archive_department", ok, time.monotonic() - start,
            f"indexed={index_count}, attachments={att_count}, after_delete={after_delete}",
        )

    def validate_laboratory_workflow(self) -> ReadinessReport:
        start = time.monotonic()
        db = self._db("lab.db")
        conn = self._seed_wal_db(db, ["samples", "results", "reports"])
        for i in range(200):
            conn.execute("INSERT INTO samples VALUES (?, ?)", (i, f"sample_{i}"))
        conn.commit()
        for i in range(200):
            conn.execute("UPDATE samples SET val='analyzed' WHERE id=?", (i,))
            conn.execute("INSERT INTO results VALUES (?, ?)", (i, f"result_{i}"))
        conn.commit()
        for i in range(0, 200, 2):
            conn.execute("INSERT INTO reports VALUES (?, ?)", (i, f"report_{i}"))
        conn.commit()
        analyzed = conn.execute("SELECT COUNT(*) FROM samples WHERE val='analyzed'").fetchone()[0]
        results = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
        reports = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        conn.close()
        ok = analyzed == 200 and results == 200 and reports == 100
        return ReadinessReport(
            "laboratory_workflow", ok, time.monotonic() - start,
            f"analyzed={analyzed}, results={results}, reports={reports}",
        )

    def validate_municipality_deployment(self) -> ReadinessReport:
        start = time.monotonic()
        deploy_dir = self._workspace / "municipality"
        try:
            deploy_dir.mkdir(parents=True, exist_ok=True)
            (deploy_dir / "database").mkdir(exist_ok=True)
            (deploy_dir / "attachments").mkdir(exist_ok=True)
            (deploy_dir / "logs").mkdir(exist_ok=True)
            db = deploy_dir / "database" / "municipality.db"
            conn = sqlite3.connect(str(db), timeout=5.0)
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA cache_size = -512")
            conn.execute("PRAGMA synchronous = OFF")
            conn.execute("CREATE TABLE IF NOT EXISTS citizens (id INTEGER, name TEXT)")
            for i in range(1000):
                conn.execute("INSERT INTO citizens VALUES (?, ?)", (i, f"citizen_{i}"))
            conn.commit()
            cnt = conn.execute("SELECT COUNT(*) FROM citizens").fetchone()[0]
            conn.close()
            ok = cnt == 1000
            return ReadinessReport(
                "municipality_deployment", ok, time.monotonic() - start,
                f"citizens={cnt}, low_resource=512KB cache",
            )
        except Exception as e:
            return ReadinessReport(
                "municipality_deployment", False,
                time.monotonic() - start, str(e),
            )

    def validate_low_connectivity_federation(self) -> ReadinessReport:
        start = time.monotonic()
        db = self._db("low_connectivity.db")
        conn = self._seed_wal_db(db, ["sync_outbox", "sync_inbox"])
        for i in range(50):
            conn.execute("INSERT INTO sync_outbox VALUES (?, ?)", (i, f"out_{i}"))
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        drained = 0
        for i in range(50):
            row = conn.execute("SELECT id, val FROM sync_outbox WHERE id=?", (i,)).fetchone()
            if row:
                conn.execute("INSERT INTO sync_inbox VALUES (?, ?)", (row[0], row[1]))
                conn.execute("DELETE FROM sync_outbox WHERE id=?", (i,))
                drained += 1
            time.sleep(0.001)
        conn.commit()
        inbox = conn.execute("SELECT COUNT(*) FROM sync_inbox").fetchone()[0]
        outbox = conn.execute("SELECT COUNT(*) FROM sync_outbox").fetchone()[0]
        conn.close()
        ok = inbox == 50 and outbox == 0
        return ReadinessReport(
            "low_connectivity_federation", ok, time.monotonic() - start,
            f"inbox={inbox}, outbox={outbox}, drained={drained}",
        )

    def validate_low_resource_workstation(self) -> ReadinessReport:
        start = time.monotonic()
        db = self._db("low_workstation.db")
        try:
            conn = sqlite3.connect(str(db), timeout=5.0)
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA cache_size = -128")
            conn.execute("PRAGMA synchronous = OFF")
            conn.execute("CREATE TABLE IF NOT EXISTS local_data (id INTEGER, payload TEXT)")
            for i in range(500):
                conn.execute("INSERT INTO local_data VALUES (?, ?)", (i, "x" * 1000))
            conn.commit()
            cnt = conn.execute("SELECT COUNT(*) FROM local_data").fetchone()[0]
            conn.close()
            ok = cnt == 500
            return ReadinessReport(
                "low_resource_workstation", ok, time.monotonic() - start,
                f"rows={cnt}, cache=128KB",
            )
        except Exception as e:
            return ReadinessReport(
                "low_resource_workstation", False,
                time.monotonic() - start, str(e),
            )

    def validate_30_day_replay(self) -> ReadinessReport:
        start = time.monotonic()
        db = self._db("thirty_day.db")
        conn = self._seed_wal_db(db, ["daily_log"])
        for day in range(30):
            for entry in range(100):
                conn.execute(
                    "INSERT INTO daily_log VALUES (?, ?)",
                    (day * 1000 + entry, f"day{day}_entry{entry}"),
                )
            conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        seqs = [r[0] for r in conn.execute("SELECT id FROM daily_log ORDER BY id").fetchall()]
        conn.close()
        monotonic = all(seqs[i] < seqs[i + 1] for i in range(len(seqs) - 1))
        ok = len(seqs) == 3000 and monotonic
        return ReadinessReport(
            "30_day_replay", ok, time.monotonic() - start,
            f"entries={len(seqs)}, monotonic={monotonic}",
        )

    def validate_deployment_recovery(self) -> ReadinessReport:
        start = time.monotonic()
        db = self._db("recovery.db")
        conn = self._seed_wal_db(db, ["recovery_test"])
        conn.execute("INSERT INTO recovery_test VALUES (1, 'before_crash')")
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("INSERT INTO recovery_test VALUES (2, 'during_crash')")
        wal = db.with_suffix(".db-wal")
        if not wal.exists():
            wal = Path(str(db) + "-wal")
        if wal.exists():
            wal.unlink(missing_ok=True)
        shm = db.with_suffix(".db-shm")
        if shm.exists():
            shm.unlink(missing_ok=True)
        conn.close()
        c2 = sqlite3.connect(str(db), timeout=5.0)
        try:
            cnt = c2.execute("SELECT COUNT(*) FROM recovery_test").fetchone()[0]
            integrity = c2.execute("PRAGMA integrity_check").fetchone()
            c2.close()
            ok = integrity is not None and integrity[0] == "ok"
            return ReadinessReport(
                "deployment_recovery", ok, time.monotonic() - start,
                f"rows={cnt}, integrity={integrity}",
            )
        except Exception as e:
            return ReadinessReport("deployment_recovery", False, time.monotonic() - start, str(e))

    def validate_corruption_survival(self) -> ReadinessReport:
        start = time.monotonic()
        db = self._db("corruption_survival.db")
        conn = self._seed_wal_db(db, ["vital_data"])
        for i in range(100):
            conn.execute("INSERT INTO vital_data VALUES (?, ?)", (i, f"vital_{i}"))
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
        with open(db, "r+b") as f:
            f.seek(500)
            f.write(b"\x00" * 100)
        c2 = sqlite3.connect(str(db), timeout=5.0)
        try:
            c2.execute("SELECT COUNT(*) FROM vital_data")
            c2.close()
            integrity = False
        except Exception:
            integrity = True
        return ReadinessReport(
            "corruption_survival", integrity, time.monotonic() - start,
            f"corruption_detected={integrity}",
        )

    def validate_final_deterministic_replay(self) -> ReadinessReport:
        start = time.monotonic()
        db = self._db("final_replay.db")
        conn = self._seed_wal_db(db, ["replay_events"])
        for i in range(1000):
            conn.execute("INSERT INTO replay_events VALUES (?, ?)", (i, f"event_{i}"))
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("INSERT INTO replay_events VALUES (?, ?)", (2000, "delayed_event"))
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        seqs = [r[0] for r in conn.execute("SELECT id FROM replay_events ORDER BY id").fetchall()]
        conn.close()
        monotonic = all(seqs[i] < seqs[i + 1] for i in range(len(seqs) - 1))
        ok = len(seqs) == 1001 and monotonic
        return ReadinessReport(
            "final_deterministic_replay", ok, time.monotonic() - start,
            f"events={len(seqs)}, monotonic={monotonic}",
        )

    def validate_all(self) -> list[ReadinessReport]:
        return [
            self.validate_ministry_workflow(),
            self.validate_archive_department(),
            self.validate_laboratory_workflow(),
            self.validate_municipality_deployment(),
            self.validate_low_connectivity_federation(),
            self.validate_low_resource_workstation(),
            self.validate_30_day_replay(),
            self.validate_deployment_recovery(),
            self.validate_corruption_survival(),
            self.validate_final_deterministic_replay(),
        ]
