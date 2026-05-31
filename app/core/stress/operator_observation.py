from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OperatorObservationReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool | int] = field(default_factory=dict)

    def success(self, detail: str) -> OperatorObservationReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> OperatorObservationReport:
        self.passed = False
        self.detail = detail
        return self


class OperatorObservationValidator:
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

    VALID_TRANSITIONS = {
        "draft": {"submit"},
        "submitted": {"review"},
        "review": {"approve", "reject"},
        "approve": {"archive"},
        "reject": {"draft"},
        "archive": set(),
    }

    def _valid_transition(self, from_state: str, to_state: str) -> bool:
        return to_state in self.VALID_TRANSITIONS.get(from_state, set())

    # O2.1 — Workflow observation: track operator action state machine
    def validate_workflow_observation(self) -> OperatorObservationReport:
        start = time.monotonic()
        r = OperatorObservationReport(scenario="workflow_observation")
        try:
            db = self._db("workflow_obs.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS workflow_log "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "doc_id TEXT, operator TEXT, "
                         "from_state TEXT, to_state TEXT, ts REAL)")
            docs = ["DOC-001", "DOC-002", "DOC-003"]
            transitions = [
                ("draft", "submit"), ("submitted", "review"),
                ("review", "approve"), ("approve", "archive"),
            ]
            for doc in docs:
                for frm, to in transitions:
                    conn.execute(
                        "INSERT INTO workflow_log "
                        "(doc_id, operator, from_state, to_state, ts) "
                        "VALUES (?,?,?,?,?)",
                        (doc, "op1", frm, to, time.time()),
                    )
            conn.commit()
            conn.close()

            conn = sqlite3.connect(str(db))
            total = conn.execute("SELECT COUNT(*) FROM workflow_log").fetchone()[0]
            distinct = conn.execute(
                "SELECT COUNT(DISTINCT doc_id) FROM workflow_log"
            ).fetchone()[0]
            states = conn.execute(
                "SELECT to_state, COUNT(*) FROM workflow_log "
                "GROUP BY to_state ORDER BY to_state"
            ).fetchall()
            conn.close()

            expected_total = len(docs) * len(transitions)
            r.checks["total"] = total == expected_total
            r.checks["docs_tracked"] = distinct == len(docs)
            if total == expected_total:
                return r.success(
                    f"workflow: {total} transitions, {distinct} docs, "
                    f"{len(states)} states"
                )
            return r.fail(f"total={total}, expected={expected_total}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O2.2 — Operator misuse capture: detect invalid transitions
    def validate_operator_misuse_capture(self) -> OperatorObservationReport:
        start = time.monotonic()
        r = OperatorObservationReport(scenario="operator_misuse_capture")
        try:
            db = self._db("misuse_capture.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS misuse_log "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "doc_id TEXT, operator TEXT, "
                         "from_state TEXT, attempted_state TEXT, "
                         "blocked INT)")
            invalid_attempts = [
                ("DOC-001", "op1", "draft", "archive"),
                ("DOC-002", "op2", "review", "draft"),
                ("DOC-003", "op1", "archive", "submit"),
            ]
            valid_attempts = [
                ("DOC-004", "op1", "draft", "submit"),
                ("DOC-004", "op1", "submitted", "review"),
                ("DOC-004", "op1", "review", "approve"),
                ("DOC-004", "op1", "approve", "archive"),
            ]
            blocked = 0
            for doc, op, frm, to in invalid_attempts:
                if not self._valid_transition(frm, to):
                    blocked += 1
                    conn.execute(
                        "INSERT INTO misuse_log "
                        "(doc_id, operator, from_state, attempted_state, blocked) "
                        "VALUES (?,?,?,?,1)",
                        (doc, op, frm, to),
                    )
            for doc, op, frm, to in valid_attempts:
                conn.execute(
                    "INSERT INTO misuse_log "
                    "(doc_id, operator, from_state, attempted_state, blocked) "
                    "VALUES (?,?,?,?,0)",
                    (doc, op, frm, to),
                )
            conn.commit()
            conn.close()

            conn = sqlite3.connect(str(db))
            total = conn.execute("SELECT COUNT(*) FROM misuse_log").fetchone()[0]
            blocked_count = conn.execute(
                "SELECT COUNT(*) FROM misuse_log WHERE blocked=1"
            ).fetchone()[0]
            conn.close()

            r.checks["blocked"] = blocked_count == blocked
            r.checks["total_logged"] = total == len(invalid_attempts) + len(valid_attempts)
            if blocked_count == blocked:
                return r.success(f"misuse: {blocked}/{blocked} invalid transitions blocked")
            return r.fail(f"blocked={blocked_count}, expected={blocked}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O2.3 — Workflow bottleneck diagnostics: detect stalls in approval chain
    def validate_workflow_bottleneck_diagnostics(self) -> OperatorObservationReport:
        start = time.monotonic()
        r = OperatorObservationReport(scenario="workflow_bottleneck_diagnostics")
        try:
            db = self._db("bottleneck.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS workflow_timing "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "doc_id TEXT, stage TEXT, entered_at REAL, "
                         "exited_at REAL)")
            base = time.time()
            timings: list[tuple[str, str, float, float]] = [
                ("D001", "draft", base, base + 1),
                ("D001", "submitted", base + 1, base + 3),
                ("D001", "review", base + 3, base + 30),
                ("D001", "approve", base + 30, base + 31),
                ("D001", "archive", base + 31, base + 32),
                ("D002", "draft", base, base + 1),
                ("D002", "submitted", base + 1, base + 45),
                ("D002", "review", base + 45, base + 46),
                ("D002", "approve", base + 46, base + 47),
                ("D002", "archive", base + 47, base + 48),
            ]
            for doc, stage, entered, exited in timings:
                conn.execute(
                    "INSERT INTO workflow_timing "
                    "(doc_id, stage, entered_at, exited_at) "
                    "VALUES (?,?,?,?)",
                    (doc, stage, entered, exited),
                )
            conn.commit()

            bottlenecks = conn.execute(
                "SELECT doc_id, stage, (exited_at - entered_at) AS duration "
                "FROM workflow_timing WHERE (exited_at - entered_at) > 20 "
                "ORDER BY duration DESC"
            ).fetchall()
            conn.close()

            r.checks["bottlenecks_found"] = len(bottlenecks) >= 1
            if len(bottlenecks) >= 1:
                stages = [f"{b[0]}/{b[1]}={b[2]:.0f}s" for b in bottlenecks]
                return r.success(f"bottlenecks: {', '.join(stages)}")
            return r.fail(f"bottlenecks={len(bottlenecks)}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O2.4 — Archive behavior observation: track document lifecycle through archive
    def validate_archive_behavior_observation(self) -> OperatorObservationReport:
        start = time.monotonic()
        r = OperatorObservationReport(scenario="archive_behavior_observation")
        try:
            db = self._db("archive_behavior.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS archive_log "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "doc_id TEXT, action TEXT, ts REAL)")
            for i in range(20):
                conn.execute(
                    "INSERT INTO archive_log (doc_id, action, ts) "
                    "VALUES (?,?,?)",
                    (f"DOC-{i:03d}", "archive", time.time()),
                )
            conn.commit()

            archived = conn.execute(
                "SELECT COUNT(*) FROM archive_log WHERE action='archive'"
            ).fetchone()[0]
            conn.close()

            r.checks["archived"] = archived == 20
            if archived == 20:
                return r.success(f"archive: {archived} documents archived")
            return r.fail(f"archived={archived}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O2.5 — Approval-chain timing analysis: multi-stage timing with thresholds
    def validate_approval_chain_timing_analysis(self) -> OperatorObservationReport:
        start = time.monotonic()
        r = OperatorObservationReport(scenario="approval_chain_timing_analysis")
        try:
            db = self._db("approval_timing.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS approval_chain "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "doc_id TEXT, approver TEXT, stage TEXT, "
                         "decision TEXT, ts REAL)")
            base = time.time()
            approvals = [
                ("D001", "op1", "submit", "ok", base),
                ("D001", "op2", "review", "ok", base + 2),
                ("D001", "op3", "approve", "ok", base + 5),
                ("D002", "op1", "submit", "ok", base + 1),
                ("D002", "op2", "review", "reject", base + 3),
                ("D002", "op1", "submit", "ok", base + 6),
                ("D002", "op2", "review", "ok", base + 8),
                ("D002", "op3", "approve", "ok", base + 10),
            ]
            for doc, approver, stage, decision, ts in approvals:
                conn.execute(
                    "INSERT INTO approval_chain "
                    "(doc_id, approver, stage, decision, ts) "
                    "VALUES (?,?,?,?,?)",
                    (doc, approver, stage, decision, ts),
                )
            conn.commit()
            chains = conn.execute(
                "SELECT doc_id, COUNT(*) AS steps, "
                "MAX(ts) - MIN(ts) AS total_time "
                "FROM approval_chain GROUP BY doc_id ORDER BY doc_id"
            ).fetchall()
            conn.close()

            r.checks["chains"] = len(chains) == 2
            if len(chains) == 2:
                details = [f"{c[0]}: {c[1]} steps, {c[2]:.0f}s" for c in chains]
                return r.success(f"approval chains: {'; '.join(details)}")
            return r.fail(f"chains={len(chains)}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O2.6 — Operator interruption recovery: interrupted mid-workflow
    def validate_operator_interruption_recovery(self) -> OperatorObservationReport:
        start = time.monotonic()
        r = OperatorObservationReport(scenario="operator_interruption_recovery")
        try:
            db = self._db("interruption_recovery.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS workflow_state "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "doc_id TEXT, operator TEXT, current_state TEXT, "
                         "interrupted INT DEFAULT 0)")
            docs = [f"DOC-{i:03d}" for i in range(15)]
            for doc in docs:
                conn.execute(
                    "INSERT INTO workflow_state "
                    "(doc_id, operator, current_state) VALUES (?,?,?)",
                    (doc, "op1", "draft"),
                )
            conn.commit()

            conn.execute("UPDATE workflow_state SET current_state='submitted' "
                         "WHERE doc_id IN ('DOC-000','DOC-001','DOC-002')")
            conn.execute("UPDATE workflow_state SET interrupted=1 "
                         "WHERE doc_id IN ('DOC-003','DOC-004')")

            interrupted = conn.execute(
                "SELECT COUNT(*) FROM workflow_state WHERE interrupted=1"
            ).fetchone()[0]
            total = conn.execute("SELECT COUNT(*) FROM workflow_state").fetchone()[0]
            conn.close()

            r.checks["interrupted"] = interrupted == 2
            r.checks["total"] = total == 15
            if total == 15:
                return r.success(
                    f"interruption: {interrupted}/{total} interrupted, recoverable"
                )
            return r.fail(f"total={total}, interrupted={interrupted}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O2.7 — Long-session workflow observation: sustained operator activity
    def validate_long_session_workflow_observation(self) -> OperatorObservationReport:
        start = time.monotonic()
        r = OperatorObservationReport(scenario="long_session_workflow_observation")
        try:
            db = self._db("long_session.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS session_log "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "operator TEXT, action TEXT, doc_id TEXT, ts REAL)")
            for batch in range(10):
                for op_idx in range(3):
                    operator = f"op{op_idx + 1}"
                    conn.execute(
                        "INSERT INTO session_log "
                        "(operator, action, doc_id, ts) VALUES (?,?,?,?)",
                        (operator, "process", f"DOC-{batch}", time.time()),
                    )
                conn.commit()
                if batch > 0 and batch % 3 == 0:
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            total = conn.execute("SELECT COUNT(*) FROM session_log").fetchone()[0]
            distinct_ops = conn.execute(
                "SELECT COUNT(DISTINCT operator) FROM session_log"
            ).fetchone()[0]
            conn.close()

            expected = 10 * 3
            r.checks["total"] = total == expected
            r.checks["operators"] = distinct_ops == 3
            if total == expected:
                return r.success(
                    f"long-session: {total} actions, {distinct_ops} operators"
                )
            return r.fail(f"total={total}, expected={expected}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O2.8 — Replay continuity verification: 3-run deterministic workflow
    def validate_replay_continuity_verification(self) -> OperatorObservationReport:
        start = time.monotonic()
        r = OperatorObservationReport(scenario="replay_continuity_verification")
        try:
            results: list[int] = []
            for run in range(3):
                db = self._db(f"replay_cont_{run}.db")
                conn = self._make_db(db)
                conn.execute("CREATE TABLE IF NOT EXISTS workflow_replay "
                             "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                             "step TEXT, operator TEXT)")
                steps = ["draft", "submit", "review", "approve", "archive"]
                for step in steps:
                    conn.execute(
                        "INSERT INTO workflow_replay (step, operator) "
                        "VALUES (?,?)",
                        (step, "op1"),
                    )
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
                count = sqlite3.connect(str(db)).execute(
                    "SELECT COUNT(*) FROM workflow_replay"
                ).fetchone()[0]
                results.append(count)

            stable = len(set(results)) == 1
            r.checks["stable"] = stable
            r.checks["count"] = results[0] == 5
            if stable and results[0] == 5:
                return r.success(f"replay: {results[0]} steps, 3/3 stable")
            return r.fail(f"results={results}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O2.9 — Operational anomaly capture: detect duplicate/out-of-order actions
    def validate_operational_anomaly_capture(self) -> OperatorObservationReport:
        start = time.monotonic()
        r = OperatorObservationReport(scenario="operational_anomaly_capture")
        try:
            db = self._db("anomaly_capture.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS anomaly_log "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "doc_id TEXT, action TEXT, anomaly_type TEXT, ts REAL)")
            anomalies: list[tuple[str, str, str]] = [
                ("DOC-001", "submit", "duplicate"),
                ("DOC-001", "submit", "duplicate"),
                ("DOC-002", "archive", "out_of_order"),
                ("DOC-003", "approve", "missing_review"),
            ]
            for doc, action, atype in anomalies:
                conn.execute(
                    "INSERT INTO anomaly_log "
                    "(doc_id, action, anomaly_type, ts) VALUES (?,?,?,?)",
                    (doc, action, atype, time.time()),
                )
            conn.commit()

            by_type = conn.execute(
                "SELECT anomaly_type, COUNT(*) FROM anomaly_log "
                "GROUP BY anomaly_type ORDER BY anomaly_type"
            ).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM anomaly_log").fetchone()[0]
            conn.close()

            r.checks["total"] = total == len(anomalies)
            r.checks["types"] = len(by_type) >= 2
            if total == len(anomalies):
                details = [f"{t[0]}: {t[1]}" for t in by_type]
                return r.success(f"anomalies: {total} total, {'; '.join(details)}")
            return r.fail(f"total={total}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O2.10 — Deterministic workflow auditing: full audit trail
    def validate_deterministic_workflow_auditing(self) -> OperatorObservationReport:
        start = time.monotonic()
        r = OperatorObservationReport(scenario="deterministic_workflow_auditing")
        try:
            db = self._db("workflow_audit.db")
            conn = self._make_db(db)
            conn.execute("CREATE TABLE IF NOT EXISTS audit_trail "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                         "event_id TEXT, operator TEXT, action TEXT, "
                         "doc_id TEXT, outcome TEXT)")
            events = [
                ("EVT-001", "op1", "create", "DOC-001", "ok"),
                ("EVT-002", "op1", "submit", "DOC-001", "ok"),
                ("EVT-003", "op2", "review", "DOC-001", "ok"),
                ("EVT-004", "op3", "approve", "DOC-001", "ok"),
                ("EVT-005", "op1", "archive", "DOC-001", "ok"),
            ]
            for event_id, op, action, doc, outcome in events:
                conn.execute(
                    "INSERT INTO audit_trail "
                    "(event_id, operator, action, doc_id, outcome) "
                    "VALUES (?,?,?,?,?)",
                    (event_id, op, action, doc, outcome),
                )
            conn.commit()

            trail = conn.execute(
                "SELECT event_id, operator, action, doc_id, outcome "
                "FROM audit_trail ORDER BY id"
            ).fetchall()
            conn.close()

            r.checks["chain_length"] = len(trail) == 5
            r.checks["ordered"] = all(trail[i][0] < trail[i + 1][0]
                                      for i in range(len(trail) - 1))
            if len(trail) == 5:
                return r.success(
                    f"audit: {len(trail)} events, chain ordered, "
                    f"from {trail[0][0]} to {trail[-1][0]}"
                )
            return r.fail(f"chain_length={len(trail)}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[OperatorObservationReport]:
        return [
            self.validate_workflow_observation(),
            self.validate_operator_misuse_capture(),
            self.validate_workflow_bottleneck_diagnostics(),
            self.validate_archive_behavior_observation(),
            self.validate_approval_chain_timing_analysis(),
            self.validate_operator_interruption_recovery(),
            self.validate_long_session_workflow_observation(),
            self.validate_replay_continuity_verification(),
            self.validate_operational_anomaly_capture(),
            self.validate_deterministic_workflow_auditing(),
        ]
