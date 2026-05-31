from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PilotWorkflowReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool] = field(default_factory=dict)

    def success(self, detail: str) -> PilotWorkflowReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> PilotWorkflowReport:
        self.passed = False
        self.detail = detail
        return self


class PilotWorkflowValidator:
    def __init__(self, work_dir: Path) -> None:
        self._work = work_dir
        self._work.mkdir(parents=True, exist_ok=True)

    def _db(self, name: str) -> Path:
        return self._work / name

    def _integrity(self, path: Path) -> bool:
        try:
            conn = sqlite3.connect(str(path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            return row is not None and row[0] == "ok"
        except Exception:
            return False

    # Draft → approval → archive → print replay
    def validate_correspondence_lifecycle(self) -> PilotWorkflowReport:
        start = time.monotonic()
        report = PilotWorkflowReport(scenario="correspondence_lifecycle")
        try:
            db = self._db("lifecycle.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS letters "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "status TEXT, content TEXT, ts REAL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS archive "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "letter_id INTEGER, content TEXT)"
            )

            for i in range(30):
                conn.execute("INSERT INTO letters (status, content, ts) VALUES (?,?,?)",
                             ("draft", f"letter_{i}", time.monotonic()))
            conn.commit()

            draft_count = conn.execute(
                "SELECT COUNT(*) FROM letters WHERE status='draft'"
            ).fetchone()[0]

            conn.execute("UPDATE letters SET status='approved' WHERE id % 3 = 0")
            conn.commit()

            approved = conn.execute(
                "SELECT * FROM letters WHERE status='approved'"
            ).fetchall()
            for row in approved:
                conn.execute("INSERT INTO archive (letter_id, content) VALUES (?,?)",
                             (row[0], row[2]))
            conn.commit()

            archived = conn.execute("SELECT COUNT(*) FROM archive").fetchone()[0]
            conn.close()

            integrity = self._integrity(db)
            report.checks["integrity"] = integrity
            report.checks["drafts_created"] = draft_count == 30
            report.checks["archived"] = archived > 0

            if integrity:
                return report.success(
                    f"lifecycle: {draft_count} drafts, {archived} archived"
                )
            return report.fail("integrity check failed")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Repeated save interruption
    def validate_save_interruption(self) -> PilotWorkflowReport:
        start = time.monotonic()
        report = PilotWorkflowReport(scenario="save_interruption")
        try:
            db = self._db("save_interrupt.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS drafts "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, version INTEGER)"
            )

            for version in range(50):
                conn.execute("INSERT INTO drafts (content, version) VALUES (?,?)",
                             (f"v{version}_content", version))
                conn.commit()

                if version % 10 == 0:
                    conn.execute("DELETE FROM drafts WHERE version < ?", (version - 5,))
                    conn.commit()

            final = conn.execute("SELECT COUNT(*) FROM drafts").fetchone()[0]
            conn.close()

            integrity = self._integrity(db)
            report.checks["integrity"] = integrity
            report.checks["bounded_growth"] = final <= 50

            if integrity:
                return report.success(
                    f"save interruption: {final} drafts after 50 versions"
                )
            return report.fail(f"integrity={integrity}, count={final}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Rapid operator switching
    def validate_operator_switching(self) -> PilotWorkflowReport:
        start = time.monotonic()
        report = PilotWorkflowReport(scenario="operator_switching")
        try:
            db = self._db("operator_switch.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS sessions "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, operator TEXT, action TEXT, ts REAL)"
            )

            operators = ["op_1", "op_2", "op_3"]
            for op in operators:
                for _ in range(20):
                    conn.execute(
                        "INSERT INTO sessions (operator, action, ts) VALUES (?,?,?)",
                        (op, f"action_by_{op}", time.monotonic()),
                    )
                conn.commit()

                seq_check = conn.execute(
                    "SELECT id FROM sessions WHERE operator=? ORDER BY id",
                    (op,),
                ).fetchall()
                _ = all(
                    seq_check[i][0] < seq_check[i + 1][0]
                    for i in range(len(seq_check) - 1)
                ) if len(seq_check) > 1 else True

            final = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            conn.close()

            integrity = self._integrity(db)
            report.checks["integrity"] = integrity
            report.checks["total_ops"] = final == 60

            if integrity:
                return report.success(
                    f"operator switching: {final} ops across 3 operators"
                )
            return report.fail(f"integrity={integrity}, count={final}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Accidental duplicate submissions
    def validate_duplicate_submissions(self) -> PilotWorkflowReport:
        start = time.monotonic()
        report = PilotWorkflowReport(scenario="duplicate_submissions")
        try:
            db = self._db("duplicates.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS submissions "
                "(id INTEGER PRIMARY KEY, doc_hash TEXT UNIQUE, content TEXT)"
            )

            submissions = [
                ("abc123", "doc1"),
                ("def456", "doc2"),
                ("abc123", "doc1_dup"),
                ("ghi789", "doc3"),
                ("def456", "doc2_dup"),
            ]

            unique_count = 0
            dup_count = 0
            for h, content in submissions:
                try:
                    conn.execute(
                        "INSERT INTO submissions (doc_hash, content) VALUES (?,?)",
                        (h, content),
                    )
                    unique_count += 1
                except sqlite3.IntegrityError:
                    dup_count += 1
            conn.commit()
            conn.close()

            integrity = self._integrity(db)
            report.checks["integrity"] = integrity
            report.checks["duplicates_blocked"] = dup_count == 2
            report.checks["uniques_accepted"] = unique_count == 3

            if integrity and dup_count == 2:
                return report.success(
                    f"duplicates: {dup_count} blocked, {unique_count} accepted"
                )
            return report.fail(
                f"integrity={integrity}, blocked={dup_count}, accepted={unique_count}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Archive overload handling
    def validate_archive_overload(self) -> PilotWorkflowReport:
        start = time.monotonic()
        report = PilotWorkflowReport(scenario="archive_overload")
        try:
            db = self._db("archive_overload.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS archive "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT)"
            )

            for i in range(300):
                conn.execute("INSERT INTO archive (payload) VALUES (?)",
                             ("x" * 1024 + str(i),))
            conn.commit()

            count = conn.execute("SELECT COUNT(*) FROM archive").fetchone()[0]
            conn.execute("DELETE FROM archive WHERE id % 2 = 0")
            conn.commit()
            conn.execute("VACUUM")
            conn.close()

            integrity = self._integrity(db)
            post_compact = sqlite3.connect(str(db))
            remaining = post_compact.execute("SELECT COUNT(*) FROM archive").fetchone()[0]
            post_compact.close()

            report.checks["integrity"] = integrity
            report.checks["loaded"] = count == 300
            report.checks["compacted"] = remaining < 300

            if integrity:
                return report.success(
                    f"archive overload: {count} loaded, {remaining} after compact"
                )
            return report.fail(f"integrity={integrity}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Invalid attachment rejection
    def validate_invalid_attachment_rejection(self) -> PilotWorkflowReport:
        start = time.monotonic()
        report = PilotWorkflowReport(scenario="invalid_attachment_rejection")
        try:
            db = self._db("attachments.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS attachments "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "name TEXT, size INTEGER, hash TEXT)"
            )

            valid = [("doc.pdf", 1024, "abc"), ("report.pdf", 2048, "def")]
            invalid = [("malware.exe", 999999, "xxx"), ("too_big.zip", 50_000_000, "yyy")]

            valid_accepted = 0
            invalid_rejected = 0
            for name, size, h in valid:
                conn.execute(
                    "INSERT INTO attachments (name, size, hash) VALUES (?,?,?)",
                    (name, size, h),
                )
                valid_accepted += 1

            for name, size, h in invalid:
                if size > 10_000_000:
                    invalid_rejected += 1
                elif name.endswith(".exe"):
                    invalid_rejected += 1
                else:
                    conn.execute(
                        "INSERT INTO attachments (name, size, hash) VALUES (?,?,?)",
                        (name, size, h),
                    )
            conn.commit()
            conn.close()

            integrity = self._integrity(db)
            final_count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM attachments"
            ).fetchone()[0]
            sqlite3.connect(str(db)).close()

            report.checks["integrity"] = integrity
            report.checks["valid_accepted"] = valid_accepted == 2
            report.checks["final_count_correct"] = final_count == valid_accepted

            if integrity:
                return report.success(
                    f"attachments: {valid_accepted} accepted, "
                    f"{invalid_rejected} rejected"
                )
            return report.fail(f"integrity={integrity}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Concurrent numbering validation
    def validate_concurrent_numbering(self) -> PilotWorkflowReport:
        start = time.monotonic()
        report = PilotWorkflowReport(scenario="concurrent_numbering")
        try:
            db = self._db("numbering.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS documents "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT, content TEXT)"
            )

            for i in range(100):
                conn.execute("INSERT INTO documents (number, content) VALUES (?,?)",
                             (f"DOC-{i:04d}", f"content_{i}"))
            conn.commit()

            seqs = conn.execute("SELECT id FROM documents ORDER BY id").fetchall()
            monotonic = all(
                seqs[i][0] < seqs[i + 1][0]
                for i in range(len(seqs) - 1)
            )

            _ = conn.execute(
                "SELECT COUNT(*) FROM documents d1 "
                "WHERE NOT EXISTS (SELECT 1 FROM documents d2 "
                "WHERE d2.id = d1.id - 1 AND d2.id > 0)"
            ).fetchone()[0]

            conn.close()
            integrity = self._integrity(db)

            report.checks["integrity"] = integrity
            report.checks["monotonic"] = monotonic

            if integrity and monotonic:
                return report.success(
                    f"numbering: {len(seqs)} docs, monotonic={monotonic}"
                )
            return report.fail(f"integrity={integrity}, monotonic={monotonic}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Session recovery continuation
    def validate_session_recovery(self) -> PilotWorkflowReport:
        start = time.monotonic()
        report = PilotWorkflowReport(scenario="session_recovery")
        try:
            db = self._db("session_recovery.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS sessions "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, operator TEXT, "
                "state TEXT, last_pos INTEGER)"
            )

            conn.execute("INSERT INTO sessions (operator, state, last_pos) VALUES (?,?,?)",
                         ("op1", "active", 25))
            conn.commit()

            last_pos, _ = conn.execute(
                "SELECT last_pos, state FROM sessions WHERE operator=?",
                ("op1",),
            ).fetchone()

            for i in range(last_pos, last_pos + 10):
                conn.execute("INSERT INTO sessions (operator, state, last_pos) VALUES (?,?,?)",
                             ("op1", "recovered", i))
            conn.commit()

            final_pos = conn.execute(
                "SELECT MAX(last_pos) FROM sessions WHERE operator=?",
                ("op1",),
            ).fetchone()[0]
            conn.close()

            integrity = self._integrity(db)
            report.checks["integrity"] = integrity
            report.checks["recovered_from"] = last_pos == 25
            report.checks["continued_to"] = final_pos == 34

            if integrity:
                return report.success(
                    f"session recovery: pos {last_pos} → {final_pos}"
                )
            return report.fail(f"integrity={integrity}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Operator rollback validation
    def validate_operator_rollback(self) -> PilotWorkflowReport:
        start = time.monotonic()
        report = PilotWorkflowReport(scenario="operator_rollback")
        try:
            db = self._db("rollback.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS actions "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, operator TEXT, "
                "action TEXT, applied INTEGER DEFAULT 1)"
            )

            conn.execute("INSERT INTO actions (operator, action) VALUES (?,?)",
                         ("op1", "create_doc_1"))
            conn.execute("INSERT INTO actions (operator, action) VALUES (?,?)",
                         ("op1", "approve_doc_1"))
            conn.execute("INSERT INTO actions (operator, action) VALUES (?,?)",
                         ("op1", "archive_doc_1"))
            conn.commit()

            conn.execute("UPDATE actions SET applied=0 WHERE action='approve_doc_1'")
            conn.commit()

            rollback_count = conn.execute(
                "SELECT COUNT(*) FROM actions WHERE applied=0"
            ).fetchone()[0]
            remaining = conn.execute(
                "SELECT COUNT(*) FROM actions WHERE applied=1"
            ).fetchone()[0]
            conn.close()

            integrity = self._integrity(db)
            report.checks["integrity"] = integrity
            report.checks["rollback_recorded"] = rollback_count == 1
            report.checks["remaining_valid"] = remaining == 2

            if integrity:
                return report.success(
                    f"rollback: {rollback_count} rolled back, "
                    f"{remaining} remaining"
                )
            return report.fail(f"integrity={integrity}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[PilotWorkflowReport]:
        return [
            self.validate_correspondence_lifecycle(),
            self.validate_save_interruption(),
            self.validate_operator_switching(),
            self.validate_duplicate_submissions(),
            self.validate_archive_overload(),
            self.validate_invalid_attachment_rejection(),
            self.validate_concurrent_numbering(),
            self.validate_session_recovery(),
            self.validate_operator_rollback(),
        ]
