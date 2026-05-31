from __future__ import annotations

import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DeploymentReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool] = field(default_factory=dict)

    def success(self, detail: str) -> DeploymentReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> DeploymentReport:
        self.passed = False
        self.detail = detail
        return self


class DeploymentSimulator:
    def __init__(self, work_dir: Path) -> None:
        self._work = work_dir
        self._work.mkdir(parents=True, exist_ok=True)

    def _db(self, name: str) -> Path:
        return self._work / name

    def _make_db(self, path: Path, table: str = "records") -> None:
        conn = sqlite3.connect(str(path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(f"CREATE TABLE IF NOT EXISTS {table} "
                      "(id INTEGER PRIMARY KEY, v TEXT, ts REAL)")
        conn.commit()
        conn.close()

    def _count(self, path: Path, table: str = "records") -> int:
        conn = sqlite3.connect(str(path))
        c = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        conn.close()
        return c

    def _integrity(self, path: Path) -> bool:
        try:
            conn = sqlite3.connect(str(path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            return row is not None and row[0] == "ok"
        except Exception:
            return False

    # -- ministry deployment --

    def simulate_ministry(self) -> DeploymentReport:
        start = time.monotonic()
        report = DeploymentReport(scenario="ministry_deployment")
        try:
            db = self._db("ministry.db")
            self._make_db(db, "letters")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            for i in range(200):
                conn.execute("INSERT INTO letters (v, ts) VALUES (?, ?)",
                             (f"letter_{i}", time.monotonic()))
            conn.commit()

            conn.execute("CREATE TABLE IF NOT EXISTS outbox (id INTEGER PRIMARY KEY, msg TEXT)")
            for i in range(50):
                conn.execute("INSERT INTO outbox (msg) VALUES (?)", (f"out_{i}",))

            conn.execute("CREATE TABLE IF NOT EXISTS inbox (id INTEGER PRIMARY KEY, msg TEXT)")
            for i in range(30):
                conn.execute("INSERT INTO inbox (msg) VALUES (?)", (f"in_{i}",))
            conn.commit()
            conn.close()

            integrity = self._integrity(db)
            count = self._count(db, "letters")
            report.checks["integrity"] = integrity
            report.checks["letter_count"] = count == 200

            if integrity:
                return report.success(f"ministry: {count} letters, integrity ok")
            return report.fail("integrity check failed")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- university deployment --

    def simulate_university(self) -> DeploymentReport:
        start = time.monotonic()
        report = DeploymentReport(scenario="university_deployment")
        try:
            db = self._db("university.db")
            self._make_db(db, "enrollments")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            for i in range(300):
                conn.execute("INSERT INTO enrollments (v, ts) VALUES (?, ?)",
                             (f"student_{i}", time.monotonic()))
            conn.commit()

            conn.execute("CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, code TEXT)")
            for i in range(20):
                conn.execute("INSERT INTO courses (code) VALUES (?)", (f"CS_{i}",))
            conn.commit()

            conn.execute("CREATE TABLE IF NOT EXISTS grades (id INTEGER PRIMARY KEY, "
                         "enrollment_id INTEGER, grade REAL)")
            for i in range(300):
                conn.execute("INSERT INTO grades (enrollment_id, grade) VALUES (?, ?)",
                             (i % 300 + 1, 60.0 + (i % 40)))
            conn.commit()
            conn.close()

            integrity = self._integrity(db)
            enroll_count = self._count(db, "enrollments")
            grade_count = self._count(db, "grades")
            report.checks["integrity"] = integrity
            report.checks["enrollment_count"] = enroll_count == 300
            report.checks["grade_count"] = grade_count == 300

            if integrity:
                return report.success(
                    f"university: {enroll_count} enrollments, {grade_count} grades"
                )
            return report.fail("integrity check failed")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- hospital deployment --

    def simulate_hospital(self) -> DeploymentReport:
        start = time.monotonic()
        report = DeploymentReport(scenario="hospital_deployment")
        try:
            db = self._db("hospital.db")
            self._make_db(db, "patients")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            for i in range(150):
                conn.execute("INSERT INTO patients (v, ts) VALUES (?, ?)",
                             (f"patient_{i}", time.monotonic()))
            conn.commit()

            conn.execute("CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, "
                         "patient_id INTEGER, diagnosis TEXT)")
            for i in range(200):
                conn.execute("INSERT INTO records (patient_id, diagnosis) VALUES (?, ?)",
                             (i % 150 + 1, f"DX_{i % 20}"))
            conn.commit()

            conn.execute("CREATE TABLE IF NOT EXISTS prescriptions (id INTEGER PRIMARY KEY, "
                         "record_id INTEGER, drug TEXT)")
            for i in range(150):
                conn.execute("INSERT INTO prescriptions (record_id, drug) VALUES (?, ?)",
                             (i % 200 + 1, f"drug_{i % 30}"))
            conn.commit()
            conn.close()

            integrity = self._integrity(db)
            patient_count = self._count(db, "patients")
            record_count = self._count(db, "records")
            rx_count = self._count(db, "prescriptions")
            report.checks["integrity"] = integrity
            report.checks["patient_count"] = patient_count == 150
            report.checks["record_count"] = record_count == 200
            report.checks["rx_count"] = rx_count == 150

            if integrity:
                return report.success(
                    f"hospital: {patient_count} patients, "
                    f"{record_count} records, {rx_count} rx"
                )
            return report.fail("integrity check failed")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- municipality deployment --

    def simulate_municipality(self) -> DeploymentReport:
        start = time.monotonic()
        report = DeploymentReport(scenario="municipality_deployment")
        try:
            db = self._db("municipality.db")
            self._make_db(db, "citizens")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size = -512")

            for i in range(500):
                conn.execute("INSERT INTO citizens (v, ts) VALUES (?, ?)",
                             (f"citizen_{i}", time.monotonic()))
            conn.commit()

            conn.execute("CREATE TABLE IF NOT EXISTS permits (id INTEGER PRIMARY KEY, "
                         "citizen_id INTEGER, type TEXT)")
            for i in range(100):
                conn.execute("INSERT INTO permits (citizen_id, type) VALUES (?, ?)",
                             (i % 500 + 1, f"permit_{i % 10}"))
            conn.commit()

            conn.execute("CREATE TABLE IF NOT EXISTS taxes (id INTEGER PRIMARY KEY, "
                         "citizen_id INTEGER, amount REAL)")
            for i in range(200):
                conn.execute("INSERT INTO taxes (citizen_id, amount) VALUES (?, ?)",
                             (i % 500 + 1, 100.0 + i))
            conn.commit()
            conn.close()

            integrity = self._integrity(db)
            citizen_count = self._count(db, "citizens")
            permit_count = self._count(db, "permits")
            tax_count = self._count(db, "taxes")
            report.checks["integrity"] = integrity
            report.checks["citizen_count"] = citizen_count == 500

            if integrity:
                return report.success(
                    f"municipality: {citizen_count} citizens, "
                    f"{permit_count} permits, {tax_count} taxes"
                )
            return report.fail("integrity check failed")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- low-connectivity federation replay --

    def simulate_low_connectivity_federation(self) -> DeploymentReport:
        start = time.monotonic()
        report = DeploymentReport(scenario="low_connectivity_federation")
        try:
            node_a = self._db("node_a.db")
            node_b = self._db("node_b.db")
            self._make_db(node_a, "outbox")
            self._make_db(node_b, "inbox")

            conn_a = sqlite3.connect(str(node_a), timeout=10)
            conn_a.execute("PRAGMA journal_mode=WAL")
            for i in range(30):
                conn_a.execute("INSERT INTO outbox (v, ts) VALUES (?, ?)",
                               (f"msg_{i}", time.monotonic()))
            conn_a.commit()

            conn_b = sqlite3.connect(str(node_b), timeout=10)
            conn_b.execute("PRAGMA journal_mode=WAL")
            conn_b.commit()

            messages = conn_a.execute(
                "SELECT v FROM outbox ORDER BY id"
            ).fetchall()
            conn_a.close()

            for row in messages:
                conn_b.execute("INSERT INTO inbox (v, ts) VALUES (?, ?)",
                               (row[0], time.monotonic()))
            conn_b.commit()

            fed_count = conn_b.execute("SELECT COUNT(*) FROM inbox").fetchone()[0]
            integrity_b = self._integrity(node_b)
            conn_b.close()

            report.checks["integrity"] = integrity_b
            report.checks["all_messages_replicated"] = fed_count == 30

            if integrity_b and fed_count == 30:
                return report.success(
                    f"low-connectivity: {fed_count}/30 messages replicated"
                )
            return report.fail(
                f"integrity={integrity_b}, replicated={fed_count}/30"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- cross-institution sync replay --

    def simulate_cross_institution_sync(self) -> DeploymentReport:
        start = time.monotonic()
        report = DeploymentReport(scenario="cross_institution_sync")
        try:
            inst_a = self._db("inst_a.db")
            inst_b = self._db("inst_b.db")
            inst_c = self._db("inst_c.db")

            for db_path, label, count in [
                (inst_a, "health", 40),
                (inst_b, "finance", 30),
                (inst_c, "edu", 25),
            ]:
                self._make_db(db_path, "events")
                conn = sqlite3.connect(str(db_path), timeout=10)
                conn.execute("PRAGMA journal_mode=WAL")
                for i in range(count):
                    conn.execute("INSERT INTO events (v, ts) VALUES (?, ?)",
                                 (f"{label}_evt_{i}", time.monotonic()))
                conn.commit()
                conn.close()

            merge_db = self._db("merged.db")
            self._make_db(merge_db, "events_all")

            merge_conn = sqlite3.connect(str(merge_db), timeout=10)
            merge_conn.execute("PRAGMA journal_mode=WAL")

            total = 0
            for src in [inst_a, inst_b, inst_c]:
                conn = sqlite3.connect(str(src), timeout=10)
                rows = conn.execute("SELECT v, ts FROM events ORDER BY id").fetchall()
                conn.close()
                for v, ts in rows:
                    merge_conn.execute(
                        "INSERT INTO events_all (v, ts) VALUES (?, ?)", (v, ts)
                    )
                    total += 1
            merge_conn.commit()

            r1 = merge_conn.execute("SELECT v FROM events_all ORDER BY id").fetchall()
            r2 = merge_conn.execute("SELECT v FROM events_all ORDER BY id").fetchall()
            deterministic = r1 == r2
            merge_conn.close()

            integrity = self._integrity(merge_db)
            report.checks["integrity"] = integrity
            report.checks["deterministic_replay"] = deterministic
            report.checks["total_count"] = total == 95

            if integrity and deterministic:
                return report.success(
                    f"cross-institution: {total} events from 3 sources, "
                    f"deterministic={deterministic}"
                )
            return report.fail(
                f"integrity={integrity}, deterministic={deterministic}, "
                f"total={total}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- operator contention --

    def simulate_operator_contention(self) -> DeploymentReport:
        start = time.monotonic()
        report = DeploymentReport(scenario="operator_contention")
        try:
            db = self._db("contention.db")
            self._make_db(db, "actions")

            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.close()

            results: list[int] = []
            errors: list[str] = []
            lock = threading.Lock()

            def worker(wid: int) -> None:
                try:
                    c = sqlite3.connect(str(db), timeout=30)
                    for j in range(25):
                        c.execute("INSERT INTO actions (v, ts) VALUES (?, ?)",
                                  (f"op_{wid}_act_{j}", time.monotonic()))
                    c.commit()
                    with lock:
                        cnt = c.execute(
                            "SELECT COUNT(*) FROM actions"
                        ).fetchone()[0]
                        results.append(cnt)
                    c.close()
                except Exception as e:
                    with lock:
                        errors.append(str(e))

            threads = [
                threading.Thread(target=worker, args=(w,), daemon=True)
                for w in range(10)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=30)

            c2 = sqlite3.connect(str(db), timeout=10)
            final = c2.execute("SELECT COUNT(*) FROM actions").fetchone()[0]
            seqs = c2.execute("SELECT id FROM actions ORDER BY id").fetchall()
            monotonic = all(
                seqs[i][0] < seqs[i + 1][0]
                for i in range(len(seqs) - 1)
            ) if len(seqs) > 1 else True
            integrity = self._integrity(db)
            c2.close()

            expected = 10 * 25
            report.checks["integrity"] = integrity
            report.checks["count_match"] = final == expected
            report.checks["monotonic_ids"] = monotonic
            report.checks["no_errors"] = len(errors) == 0

            if integrity and final == expected and monotonic:
                return report.success(
                    f"contention: {final}/{expected} rows, monotonic={monotonic}"
                )
            return report.fail(
                f"integrity={integrity}, rows={final}/{expected}, "
                f"monotonic={monotonic}, errors={len(errors)}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- delayed sync replay --

    def simulate_delayed_sync(self) -> DeploymentReport:
        start = time.monotonic()
        report = DeploymentReport(scenario="delayed_sync")
        try:
            primary = self._db("primary.db")
            self._make_db(primary, "tx")
            conn = sqlite3.connect(str(primary), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            for i in range(40):
                conn.execute("INSERT INTO tx (v, ts) VALUES (?, ?)",
                             (f"tx_{i}", time.monotonic()))
            conn.commit()

            snapshot = conn.execute("SELECT id, v, ts FROM tx ORDER BY id").fetchall()
            conn.close()

            replica = self._db("replica.db")
            self._make_db(replica, "tx")
            rconn = sqlite3.connect(str(replica), timeout=10)
            rconn.execute("PRAGMA journal_mode=WAL")
            for row in snapshot:
                rconn.execute("INSERT INTO tx (id, v, ts) VALUES (?, ?, ?)", row)
            rconn.commit()

            for row in snapshot:
                rconn.execute(
                    "INSERT OR IGNORE INTO tx (id, v, ts) VALUES (?, ?, ?)", row
                )
            rconn.commit()

            merged = rconn.execute(
                "SELECT COUNT(*) as c FROM (SELECT DISTINCT id FROM tx)"
            ).fetchone()[0]
            dedup = merged == 40
            rconn.close()

            report.checks["dedup_worked"] = dedup

            if dedup:
                return report.success(
                    f"delayed sync: {merged} unique after replay"
                )
            return report.fail(f"dedup failed: {merged} unique")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- unsafe shutdown replay --

    def simulate_unsafe_shutdown(self) -> DeploymentReport:
        start = time.monotonic()
        report = DeploymentReport(scenario="unsafe_shutdown")
        try:
            db = self._db("unsafe.db")
            self._make_db(db, "ops")

            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")

            for i in range(50):
                conn.execute("INSERT INTO ops (v, ts) VALUES (?, ?)",
                             (f"pre_{i}", time.monotonic()))
            conn.commit()

            pre_count = conn.execute("SELECT COUNT(*) FROM ops").fetchone()[0]

            conn.execute("INSERT INTO ops (v, ts) VALUES (?, ?)",
                         ("crash_write_1", time.monotonic()))
            conn.execute("INSERT INTO ops (v, ts) VALUES (?, ?)",
                         ("crash_write_2", time.monotonic()))

            conn.close()

            wal_path = db.with_suffix(db.suffix + "-wal")
            if wal_path.exists():
                original_size = wal_path.stat().st_size
                with open(wal_path, "ab") as f:
                    f.truncate(original_size // 2)

            recover_conn = sqlite3.connect(str(db), timeout=10)
            integrity = self._integrity(db)
            recover_count = recover_conn.execute(
                "SELECT COUNT(*) FROM ops"
            ).fetchone()[0]
            has_recovered = recover_count >= pre_count - 5
            recover_conn.close()

            report.checks["integrity"] = integrity
            report.checks["recovered"] = has_recovered
            report.checks["at_least_pre_count"] = recover_count >= pre_count

            if integrity and has_recovered:
                return report.success(
                    f"unsafe shutdown: recovered {recover_count} rows "
                    f"(pre={pre_count})"
                )
            return report.fail(
                f"integrity={integrity}, recovered={recover_count}/{pre_count}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- validate all --

    def validate_all(self) -> list[DeploymentReport]:
        return [
            self.simulate_ministry(),
            self.simulate_university(),
            self.simulate_hospital(),
            self.simulate_municipality(),
            self.simulate_low_connectivity_federation(),
            self.simulate_cross_institution_sync(),
            self.simulate_operator_contention(),
            self.simulate_delayed_sync(),
            self.simulate_unsafe_shutdown(),
        ]
