from __future__ import annotations

import hashlib
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class InstitutionReport:
    scenario: str
    passed: bool
    duration_seconds: float = 0.0
    detail: str = ""
    operator_count: int = 0
    event_count: int = 0
    audit_integrity: bool = True


class InstitutionSimulator:
    def __init__(self, workspace: Path) -> None:
        self._workspace = workspace
        self._workspace.mkdir(parents=True, exist_ok=True)

    def _db(self, name: str) -> Path:
        return self._workspace / name

    def simulate_concurrent_operators(self, operator_count: int = 50) -> InstitutionReport:
        start = time.monotonic()
        db = self._db("concurrent_ops.db")
        conn = sqlite3.connect(str(db), timeout=60.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = OFF")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS ops "
            "(id INTEGER PRIMARY KEY, operator TEXT, action TEXT, ts REAL)"
        )
        conn.close()

        results: list[int] = []
        lock = threading.Lock()

        def worker(wid: int) -> None:
            c = sqlite3.connect(str(db), timeout=30.0)
            for j in range(20):
                c.execute(
                    "INSERT INTO ops (operator, action, ts) VALUES (?, ?, ?)",
                    (f"op_{wid}", f"action_{j}", time.monotonic()),
                )
            c.commit()
            with lock:
                cnt = c.execute("SELECT COUNT(*) FROM ops").fetchone()[0]
                results.append(cnt)
            c.close()

        threads = [
            threading.Thread(target=worker, args=(w,), daemon=True)
            for w in range(operator_count)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60)

        c2 = sqlite3.connect(str(db), timeout=30.0)
        final = c2.execute("SELECT COUNT(*) FROM ops").fetchone()[0]
        seqs = c2.execute("SELECT id FROM ops ORDER BY id").fetchall()
        c2.close()
        monotonic = all(seqs[i][0] < seqs[i + 1][0] for i in range(len(seqs) - 1))
        expected = operator_count * 20
        ok = final == expected and monotonic
        return InstitutionReport(
            "concurrent_operators", ok, time.monotonic() - start,
            f"operators={operator_count}, rows={final}/{expected}",
            operator_count, final, True,
        )

    def simulate_multi_branch_federation(self) -> InstitutionReport:
        start = time.monotonic()
        branches = ["ministry_a", "ministry_b", "archive_dept", "lab_1"]
        events: dict[str, list[int]] = {b: [] for b in branches}
        for bid, branch in enumerate(branches):
            for i in range(100):
                events[branch].append(bid * 10000 + i)
        merged: list[int] = []
        for branch in branches:
            merged.extend(events[branch])
        merged.sort()
        monotonic = all(merged[i] < merged[i + 1] for i in range(len(merged) - 1))
        return InstitutionReport(
            "multi_branch_federation", monotonic, time.monotonic() - start,
            f"branches={len(branches)}, events={len(merged)}",
            event_count=len(merged), audit_integrity=monotonic,
        )

    def simulate_delayed_sync(self, delay_seconds: float = 1.0) -> InstitutionReport:
        start = time.monotonic()
        db = self._db("delayed_sync.db")
        conn = sqlite3.connect(str(db), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS sync_events "
            "(id INTEGER PRIMARY KEY, source TEXT, seq INTEGER, ts REAL)"
        )
        for i in range(50):
            conn.execute(
                "INSERT INTO sync_events (source, seq, ts) VALUES (?, ?, ?)",
                ("node_a", i, time.monotonic()),
            )
        conn.commit()
        time.sleep(delay_seconds)
        for i in range(50, 100):
            conn.execute(
                "INSERT INTO sync_events (source, seq, ts) VALUES (?, ?, ?)",
                ("node_b", i, time.monotonic()),
            )
        conn.commit()
        order = conn.execute(
            "SELECT id FROM sync_events ORDER BY id"
        ).fetchall()
        conn.close()
        monotonic = all(order[i][0] < order[i + 1][0] for i in range(len(order) - 1))
        return InstitutionReport(
            "delayed_sync", monotonic, time.monotonic() - start,
            f"delay={delay_seconds}s, events={len(order)}",
            event_count=len(order), audit_integrity=monotonic,
        )

    def simulate_archive_growth_over_time(self) -> InstitutionReport:
        start = time.monotonic()
        db = self._db("archive_growth.db")
        conn = sqlite3.connect(str(db), timeout=60.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = OFF")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS archive_log "
            "(id INTEGER PRIMARY KEY, ref TEXT, size INTEGER, ts REAL)"
        )
        conn.execute("BEGIN")
        for day in range(30):
            for doc in range(200):
                conn.execute(
                    "INSERT INTO archive_log (ref, size, ts) VALUES (?, ?, ?)",
                    (f"day{day}_doc{doc}", 1024 * (doc % 10 + 1), time.monotonic()),
                )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM archive_log").fetchone()[0]
        conn.close()
        ok = count == 6000
        return InstitutionReport(
            "archive_growth", ok, time.monotonic() - start,
            f"30 days, rows={count}", event_count=count,
        )

    def simulate_audit_replay_validation(self) -> InstitutionReport:
        start = time.monotonic()
        db = self._db("audit_replay.db")
        conn = sqlite3.connect(str(db), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS audit_log "
            "(seq INTEGER PRIMARY KEY, action TEXT, prev_hash TEXT)"
        )
        prev = "0" * 64
        for i in range(1000):
            raw = f"{prev}:{i}:action_{i}"
            h = hashlib.sha256(raw.encode()).hexdigest()
            conn.execute(
                "INSERT INTO audit_log VALUES (?, ?, ?)",
                (i, f"action_{i}", prev),
            )
            prev = h
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        rows = conn.execute(
            "SELECT seq, action, prev_hash FROM audit_log ORDER BY seq"
        ).fetchall()
        integrity = True
        expected_prev = "0" * 64
        for row in rows:
            seq, action, prev_hash = row
            if prev_hash != expected_prev:
                integrity = False
                break
            raw = f"{expected_prev}:{seq}:{action}"
            expected_prev = hashlib.sha256(raw.encode()).hexdigest()
        conn.close()
        return InstitutionReport(
            "audit_replay", integrity, time.monotonic() - start,
            f"entries={len(rows)}, integrity={integrity}",
            event_count=len(rows), audit_integrity=integrity,
        )

    def simulate_concurrent_numbering(self) -> InstitutionReport:
        start = time.monotonic()
        db = self._db("numbering.db")
        conn = sqlite3.connect(str(db), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS numbers "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, operator TEXT, ts REAL)"
        )
        conn.close()

        results: list[list[int]] = []
        lock = threading.Lock()

        def worker(wid: int) -> None:
            c = sqlite3.connect(str(db), timeout=30.0)
            mine: list[int] = []
            for _ in range(10):
                c.execute(
                    "INSERT INTO numbers (operator, ts) VALUES (?, ?)",
                    (f"op_{wid}", time.monotonic()),
                )
                mine.append(c.execute("SELECT last_insert_rowid()").fetchone()[0])
            c.commit()
            with lock:
                results.append(mine)
            c.close()

        threads = [
            threading.Thread(target=worker, args=(w,), daemon=True)
            for w in range(20)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        c2 = sqlite3.connect(str(db), timeout=30.0)
        all_ids = [r[0] for r in c2.execute("SELECT id FROM numbers ORDER BY id").fetchall()]
        c2.close()
        no_gaps = all_ids == list(range(1, len(all_ids) + 1))
        return InstitutionReport(
            "concurrent_numbering", no_gaps, time.monotonic() - start,
            f"operators=20, numbers={len(all_ids)}, no_gaps={no_gaps}",
            event_count=len(all_ids), audit_integrity=no_gaps,
        )

    def simulate_unsafe_shutdown_during_sync(self) -> InstitutionReport:
        start = time.monotonic()
        db = self._db("unsafe_sync.db")
        conn = sqlite3.connect(str(db), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS sync_state "
            "(id INTEGER PRIMARY KEY, phase TEXT, data TEXT)"
        )
        phases = ["fetch", "merge", "apply", "verify"]
        for i, phase in enumerate(phases):
            conn.execute(
                "INSERT INTO sync_state (phase, data) VALUES (?, ?)",
                (phase, f"data_{i}"),
            )
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        before = conn.execute("SELECT COUNT(*) FROM sync_state").fetchone()[0]
        conn.execute("INSERT INTO sync_state (phase, data) VALUES (?, ?)", ("commit", "final"))
        conn.execute("ROLLBACK")
        after = conn.execute("SELECT COUNT(*) FROM sync_state").fetchone()[0]
        conn.close()
        ok = before == after
        return InstitutionReport(
            "unsafe_shutdown_sync", ok, time.monotonic() - start,
            f"before={before}, after={after}, rollback_protected={ok}",
            event_count=before,
        )

    def simulate_cross_institution_replay(self) -> InstitutionReport:
        start = time.monotonic()
        db = self._db("cross_replay.db")
        conn = sqlite3.connect(str(db), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS cross_events "
            "(id INTEGER PRIMARY KEY, source TEXT, event_id TEXT, ts REAL)"
        )
        institutions = ["ministry", "archive", "lab"]
        for inst in institutions:
            for i in range(50):
                conn.execute(
                    "INSERT INTO cross_events (source, event_id, ts) "
                    "VALUES (?, ?, ?)",
                    (inst, f"{inst}_evt_{i}", time.monotonic()),
                )
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        rows = conn.execute(
            "SELECT id, source, event_id FROM cross_events ORDER BY id"
        ).fetchall()
        conn.close()
        monotonic = all(rows[i][0] < rows[i + 1][0] for i in range(len(rows) - 1))
        return InstitutionReport(
            "cross_institution_replay", monotonic, time.monotonic() - start,
            f"institutions={len(institutions)}, events={len(rows)}, ordering={monotonic}",
            event_count=len(rows),
        )

    def simulate_large_queue_replay(self) -> InstitutionReport:
        start = time.monotonic()
        db = self._db("queue_replay.db")
        conn = sqlite3.connect(str(db), timeout=60.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = OFF")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS queue "
            "(id INTEGER PRIMARY KEY, payload TEXT, seq INTEGER)"
        )
        conn.execute("BEGIN")
        for i in range(10000):
            conn.execute(
                "INSERT INTO queue (payload, seq) VALUES (?, ?)",
                (f"msg_{i}", i),
            )
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        seqs = conn.execute("SELECT seq FROM queue ORDER BY id").fetchall()
        conn.close()
        monotonic = all(seqs[i][0] < seqs[i + 1][0] for i in range(len(seqs) - 1))
        return InstitutionReport(
            "large_queue_replay", monotonic, time.monotonic() - start,
            f"messages={len(seqs)}, ordering={monotonic}",
            event_count=len(seqs),
        )

    def run_all(self) -> list[InstitutionReport]:
        return [
            self.simulate_concurrent_operators(15),
            self.simulate_multi_branch_federation(),
            self.simulate_delayed_sync(0.001),
            self.simulate_archive_growth_over_time(),
            self.simulate_audit_replay_validation(),
            self.simulate_concurrent_numbering(),
            self.simulate_unsafe_shutdown_during_sync(),
            self.simulate_cross_institution_replay(),
            self.simulate_large_queue_replay(),
        ]
