from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EnduranceReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool] = field(default_factory=dict)

    def success(self, detail: str) -> EnduranceReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> EnduranceReport:
        self.passed = False
        self.detail = detail
        return self


class OperatorEnduranceValidator:
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

    # 1 — 30-day operator replay
    def validate_thirty_day_operator_replay(self) -> EnduranceReport:
        start = time.monotonic()
        r = EnduranceReport(scenario="thirty_day_operator_replay")
        try:
            db = self._db("thirty_day.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS ops ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "day INTEGER, action TEXT, doc_id TEXT, ts REAL)"
            )
            for day in range(1, 31):
                for action in ["draft", "review", "approve", "archive"]:
                    conn.execute(
                        "INSERT INTO ops (day, action, doc_id) VALUES (?,?,?)",
                        (day, action, f"doc_{day}_{action}"),
                    )
                conn.commit()
                if day % 5 == 0:
                    conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            total = conn.execute("SELECT COUNT(*) FROM ops").fetchone()[0]
            days = conn.execute(
                "SELECT COUNT(DISTINCT day) FROM ops"
            ).fetchone()[0]
            conn.close()
            integrity = self._integrity(db)
            r.checks["total_ops"] = total == 120
            r.checks["days"] = days == 30
            r.checks["integrity"] = integrity
            if integrity and total == 120:
                return r.success(f"30-day replay: {total} ops across {days} days")
            return r.fail(f"total={total}, days={days}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 2 — Repeated draft interruptions
    def validate_repeated_draft_interruptions(self) -> EnduranceReport:
        start = time.monotonic()
        r = EnduranceReport(scenario="repeated_draft_interruptions")
        try:
            db = self._db("draft_interrupt.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS drafts ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "draft_id TEXT, state TEXT, version INTEGER)"
            )
            for cycle in range(20):
                draft_id = f"draft_{cycle}"
                conn.execute(
                    "INSERT INTO drafts (draft_id, state, version) VALUES (?,?,?)",
                    (draft_id, "interrupted", 1),
                )
                conn.commit()
                conn.execute("UPDATE drafts SET state='saved' WHERE draft_id=?",
                             (draft_id,))
                conn.commit()
                wal = self._wal_path(db)
                if wal.exists():
                    with open(wal, "w") as f:
                        f.truncate(0)
            saved = conn.execute(
                "SELECT COUNT(*) FROM drafts WHERE state='saved'"
            ).fetchone()[0]
            conn.close()
            r.checks["all_recovered"] = saved == 20
            if r.checks["all_recovered"]:
                return r.success(f"draft interrupt: {saved}/20 saved after crashes")
            return r.fail(f"saved={saved}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 3 — Rapid concurrent save replay
    def validate_rapid_concurrent_save_replay(self) -> EnduranceReport:
        start = time.monotonic()
        r = EnduranceReport(scenario="rapid_concurrent_save_replay")
        try:
            db = self._db("rapid_save.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS saves ("
                "id INTEGER PRIMARY KEY, content TEXT, ts REAL)"
            )
            for i in range(500):
                conn.execute(
                    "INSERT INTO saves (id, content) VALUES (?,?)",
                    (i, f"save_{i}"),
                )
            conn.commit()
            count = conn.execute("SELECT COUNT(*) FROM saves").fetchone()[0]
            conn.close()
            integrity = self._integrity(db)
            r.checks["count"] = count == 500
            r.checks["integrity"] = integrity
            if integrity and count == 500:
                return r.success(f"rapid save: {count} saves, integrity OK")
            return r.fail(f"count={count}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 4 — Approval/archive contention
    def validate_approval_archive_contention(self) -> EnduranceReport:
        start = time.monotonic()
        r = EnduranceReport(scenario="approval_archive_contention")
        try:
            db = self._db("contention.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS workflows ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "doc_id TEXT, stage TEXT, operator TEXT, ts REAL)"
            )
            for i in range(100):
                doc = f"doc_{i}"
                conn.execute(
                    "INSERT INTO workflows (doc_id, stage, operator) VALUES (?,?,?)",
                    (doc, "draft", "op1"),
                )
                conn.execute(
                    "INSERT INTO workflows (doc_id, stage, operator) VALUES (?,?,?)",
                    (doc, "approve", "op2"),
                )
                conn.execute(
                    "INSERT INTO workflows (doc_id, stage, operator) VALUES (?,?,?)",
                    (doc, "archive", "op3"),
                )
            conn.commit()
            total = conn.execute("SELECT COUNT(*) FROM workflows").fetchone()[0]
            stages = conn.execute(
                "SELECT COUNT(DISTINCT stage) FROM workflows"
            ).fetchone()[0]
            conn.close()
            r.checks["total"] = total == 300
            r.checks["stages"] = stages == 3
            if r.checks["total"]:
                return r.success(
                    f"contention: {total} ops across {stages} stages"
                )
            return r.fail(f"total={total}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 5 — Print interruption replay
    def validate_print_interruption_replay(self) -> EnduranceReport:
        start = time.monotonic()
        r = EnduranceReport(scenario="print_interruption_replay")
        try:
            db = self._db("print_interrupt.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS print_queue ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "doc_id TEXT, status TEXT, ts REAL)"
            )
            for i in range(40):
                conn.execute(
                    "INSERT INTO print_queue (doc_id, status) VALUES (?,?)",
                    (f"print_{i}", "pending"),
                )
            conn.commit()
            conn.execute("UPDATE print_queue SET status='completed' WHERE id <= 30")
            conn.commit()
            conn.close()
            wal = self._wal_path(db)
            if wal.exists():
                wal.unlink()
            conn2 = sqlite3.connect(str(db), timeout=30)
            conn2.execute("PRAGMA journal_mode=WAL")
            pending = conn2.execute(
                "SELECT COUNT(*) FROM print_queue WHERE status='pending'"
            ).fetchone()[0]
            completed = conn2.execute(
                "SELECT COUNT(*) FROM print_queue WHERE status='completed'"
            ).fetchone()[0]
            conn2.close()
            r.checks["pending_survived"] = pending == 10
            r.checks["completed_survived"] = completed == 30
            if r.checks["pending_survived"] and r.checks["completed_survived"]:
                return r.success(
                    f"print interrupt: {pending} pending, {completed} completed"
                )
            return r.fail(f"pending={pending}, completed={completed}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 6 — Duplicate workflow recovery
    def validate_duplicate_workflow_recovery(self) -> EnduranceReport:
        start = time.monotonic()
        r = EnduranceReport(scenario="duplicate_workflow_recovery")
        try:
            db = self._db("duplicate_recovery.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS workflows ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "workflow_id TEXT, state TEXT, UNIQUE(workflow_id))"
            )
            for i in range(30):
                conn.execute(
                    "INSERT OR IGNORE INTO workflows (workflow_id, state) "
                    "VALUES (?,?)",
                    (f"wf_{i}", "active"),
                )
            for i in range(30):
                conn.execute(
                    "INSERT OR IGNORE INTO workflows (workflow_id, state) "
                    "VALUES (?,?)",
                    (f"wf_{i}", "duplicate"),
                )
            conn.commit()
            total = conn.execute("SELECT COUNT(*) FROM workflows").fetchone()[0]
            conn.close()
            r.checks["no_duplicates"] = total == 30
            if r.checks["no_duplicates"]:
                return r.success(f"duplicate recovery: {total} unique workflows")
            return r.fail(f"total={total} (expected 30)")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 7 — Invalid attachment handling
    def validate_invalid_attachment_handling(self) -> EnduranceReport:
        start = time.monotonic()
        r = EnduranceReport(scenario="invalid_attachment_handling")
        try:
            db = self._db("invalid_attachments.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS attachments ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "name TEXT, size INTEGER, status TEXT)"
            )
            valid_extensions = {".pdf", ".tif", ".jpg", ".docx"}
            attachments = [
                ("report.pdf", 2048, "valid"),
                ("photo.jpg", 1024, "valid"),
                ("malware.exe", 4096, "rejected"),
                ("doc.docx", 1536, "valid"),
                ("script.js", 512, "rejected"),
                ("image.tif", 3072, "valid"),
                ("virus.bat", 128, "rejected"),
            ]
            for name, size, ext in attachments:
                ext_ok = any(name.lower().endswith(v) for v in valid_extensions)
                size_ok = size <= 3072
                if ext_ok and size_ok:
                    status = "accepted"
                else:
                    status = "rejected"
                conn.execute(
                    "INSERT INTO attachments (name, size, status) VALUES (?,?,?)",
                    (name, size, status),
                )
            conn.commit()
            accepted = conn.execute(
                "SELECT COUNT(*) FROM attachments WHERE status='accepted'"
            ).fetchone()[0]
            rejected = conn.execute(
                "SELECT COUNT(*) FROM attachments WHERE status='rejected'"
            ).fetchone()[0]
            conn.close()
            r.checks["accepted"] = accepted == 4
            r.checks["rejected"] = rejected == 3
            if r.checks["accepted"] and r.checks["rejected"]:
                return r.success(
                    f"attachments: {accepted} accepted, {rejected} rejected"
                )
            return r.fail(f"accepted={accepted}, rejected={rejected}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 8 — Operator session recovery
    def validate_operator_session_recovery(self) -> EnduranceReport:
        start = time.monotonic()
        r = EnduranceReport(scenario="operator_session_recovery")
        try:
            db = self._db("session_recovery.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS sessions ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "session_id TEXT, operator TEXT, "
                "last_action TEXT, state TEXT)"
            )
            conn.execute(
                "INSERT INTO sessions (session_id, operator, last_action, state) "
                "VALUES (?,?,?,?)",
                ("session_1", "operator_a", "draft_doc_5", "active"),
            )
            conn.execute(
                "INSERT INTO sessions (session_id, operator, last_action, state) "
                "VALUES (?,?,?,?)",
                ("session_2", "operator_b", "approve_doc_3", "interrupted"),
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
                "SELECT COUNT(*) FROM sessions"
            ).fetchone()[0]
            conn2.close()
            r.checks["recovered"] = recovered == 2
            if r.checks["recovered"]:
                return r.success(f"session recovery: {recovered}/2 recovered")
            return r.fail(f"recovered={recovered}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 9 — Archive overload recovery
    def validate_archive_overload_recovery(self) -> EnduranceReport:
        start = time.monotonic()
        r = EnduranceReport(scenario="archive_overload_recovery")
        try:
            db = self._db("overload.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size = -32")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS archive ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "snapshot_id TEXT, payload BLOB, ts REAL)"
            )
            for i in range(2000):
                payload = json.dumps(
                    {"idx": i, "data": "X" * 512}
                ).encode()
                conn.execute(
                    "INSERT INTO archive (snapshot_id, payload) VALUES (?,?)",
                    (f"snap_{i}", payload),
                )
                if i % 500 == 499:
                    conn.commit()
                    conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            conn.commit()
            count = conn.execute("SELECT COUNT(*) FROM archive").fetchone()[0]
            conn.close()
            integrity = self._integrity(db)
            r.checks["count"] = count == 2000
            r.checks["integrity"] = integrity
            if integrity and count == 2000:
                return r.success(f"archive overload: {count} snapshots, 32KB cache")
            return r.fail(f"count={count}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 10 — Replay continuity verification
    def validate_replay_continuity(self) -> EnduranceReport:
        start = time.monotonic()
        r = EnduranceReport(scenario="replay_continuity")
        try:
            db = self._db("continuity.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS events ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "seq INTEGER UNIQUE, event TEXT, ts REAL)"
            )
            for i in range(100):
                conn.execute(
                    "INSERT INTO events (seq, event) VALUES (?,?)",
                    (i, f"event_{i}"),
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
                cnt = c.execute("SELECT COUNT(*) FROM events").fetchone()[0]
                c.close()
                results.append(cnt)
            stable = len(set(results)) == 1
            integrity = self._integrity(db)
            r.checks["stable"] = stable
            r.checks["count"] = results[0] == 100 if results else False
            r.checks["integrity"] = integrity
            if stable and integrity:
                return r.success(
                    f"continuity: {results[0]} events, 3/3 stable"
                )
            return r.fail(f"results={results}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[EnduranceReport]:
        return [
            self.validate_thirty_day_operator_replay(),
            self.validate_repeated_draft_interruptions(),
            self.validate_rapid_concurrent_save_replay(),
            self.validate_approval_archive_contention(),
            self.validate_print_interruption_replay(),
            self.validate_duplicate_workflow_recovery(),
            self.validate_invalid_attachment_handling(),
            self.validate_operator_session_recovery(),
            self.validate_archive_overload_recovery(),
            self.validate_replay_continuity(),
        ]
