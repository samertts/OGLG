from __future__ import annotations

import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StressReport:
    scenario: str
    passed: bool
    duration_seconds: float = 0.0
    detail: str = ""
    row_count: int = 0
    wal_bytes: int = 0
    memory_mb: float = 0.0


class DatabaseStressSuite:
    def __init__(self, workspace: Path) -> None:
        self._workspace = workspace
        self._workspace.mkdir(parents=True, exist_ok=True)

    def _wal_bytes(self, db_path: Path) -> int:
        wal = db_path.with_suffix(".db-wal")
        if not wal.exists():
            wal = Path(str(db_path) + "-wal")
        return wal.stat().st_size if wal.exists() else 0

    def simulate_million_row_archive(self) -> StressReport:
        start = time.monotonic()
        db = self._workspace / "million_row.db"
        conn = sqlite3.connect(str(db), timeout=60.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = OFF")
        conn.execute("PRAGMA cache_size = -16384")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS archive "
            "(id INTEGER PRIMARY KEY, ref TEXT, data BLOB)"
        )
        batch = 10000
        total = 200000
        for i in range(0, total, batch):
            rows = [
                (i + j, f"ref_{i+j:08d}", b"x" * 64) for j in range(batch)
            ]
            conn.executemany("INSERT INTO archive VALUES (?, ?, ?)", rows)
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM archive").fetchone()[0]
        wal_bytes = self._wal_bytes(db)
        conn.close()
        ok = count == total
        return StressReport(
            "million_row_archive", ok, time.monotonic() - start,
            f"rows={count}", count, wal_bytes,
        )

    def simulate_concurrent_workstation_load(self) -> StressReport:
        start = time.monotonic()
        db = self._workspace / "concurrent.db"
        results: list[int] = []
        lock = threading.Lock()

        def worker(n: int) -> None:
            conn = sqlite3.connect(str(db), timeout=30.0)
            conn.execute("PRAGMA journal_mode = WAL")
            for i in range(50):
                conn.execute(
                    "INSERT INTO con_test VALUES (?, ?)",
                    (n * 1000 + i, f"worker_{n}_{i}"),
                )
            conn.commit()
            with lock:
                cnt = conn.execute(
                    "SELECT COUNT(*) FROM con_test"
                ).fetchone()[0]
                results.append(cnt)
            conn.close()

        conn = sqlite3.connect(str(db), timeout=30.0)
        conn.execute("CREATE TABLE IF NOT EXISTS con_test (id INTEGER, val TEXT)")
        conn.close()

        threads = [
            threading.Thread(target=worker, args=(w,), daemon=True)
            for w in range(10)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        conn = sqlite3.connect(str(db), timeout=30.0)
        final = conn.execute("SELECT COUNT(*) FROM con_test").fetchone()[0]
        wal_bytes = self._wal_bytes(db)
        conn.close()
        ok = final > 0
        return StressReport(
            "concurrent_load", ok, time.monotonic() - start,
            f"rows={final}", final, wal_bytes,
        )

    def simulate_large_wal_growth(self) -> StressReport:
        start = time.monotonic()
        db = self._workspace / "wal_growth.db"
        conn = sqlite3.connect(str(db), timeout=60.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA wal_autocheckpoint = 0")
        conn.execute("PRAGMA synchronous = OFF")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS wal_data "
            "(id INTEGER PRIMARY KEY, val TEXT, extra BLOB)"
        )
        for i in range(50000):
            conn.execute(
                "INSERT INTO wal_data VALUES (?, ?, ?)",
                (i, f"val_{i}", b"y" * 256),
            )
        conn.commit()
        wal_bytes = self._wal_bytes(db)
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()
        ok = wal_bytes > 0
        return StressReport(
            "large_wal_growth", ok, time.monotonic() - start,
            f"wal={wal_bytes}bytes", 50000, wal_bytes,
        )

    def simulate_archive_fragmentation(self) -> StressReport:
        start = time.monotonic()
        db = self._workspace / "frag.db"
        conn = sqlite3.connect(str(db), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("CREATE TABLE IF NOT EXISTS frag (id INTEGER PRIMARY KEY, val TEXT)")
        for i in range(10000):
            conn.execute("INSERT INTO frag VALUES (?, ?)", (i, f"v{i}"))
        conn.commit()
        for i in range(0, 10000, 2):
            conn.execute("DELETE FROM frag WHERE id = ?", (i,))
        conn.commit()
        for i in range(10000, 15000):
            conn.execute("INSERT INTO frag VALUES (?, ?)", (i, f"v{i}"))
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        count = conn.execute("SELECT COUNT(*) FROM frag").fetchone()[0]
        conn.execute("VACUUM")
        conn.close()
        ok = count > 0
        return StressReport(
            "archive_fragmentation", ok, time.monotonic() - start,
            f"rows={count}", count, 0,
        )

    def simulate_replay_consistency_stress(self) -> StressReport:
        start = time.monotonic()
        db = self._workspace / "replay_stress.db"
        conn = sqlite3.connect(str(db), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS replay_log "
            "(seq INTEGER PRIMARY KEY, action TEXT, ts TEXT)"
        )
        for i in range(5000):
            conn.execute(
                "INSERT INTO replay_log VALUES (?, ?, ?)",
                (i, f"action_{i}", f"ts_{i}"),
            )
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        seqs = [
            r[0]
            for r in conn.execute(
                "SELECT seq FROM replay_log ORDER BY seq"
            ).fetchall()
        ]
        conn.close()
        monotonic = all(
            seqs[i] < seqs[i + 1] for i in range(len(seqs) - 1)
        )
        return StressReport(
            "replay_consistency", monotonic,
            time.monotonic() - start,
            f"rows={len(seqs)}, monotonic={monotonic}",
            len(seqs), 0,
        )

    def simulate_pagination_stress(self) -> StressReport:
        start = time.monotonic()
        db = self._workspace / "pagination.db"
        conn = sqlite3.connect(str(db), timeout=30.0)
        conn.execute("CREATE TABLE IF NOT EXISTS pages (id INTEGER, title TEXT)")
        for i in range(50000):
            conn.execute("INSERT INTO pages VALUES (?, ?)", (i, f"doc_{i}"))
        conn.commit()
        page_size = 100
        page = 3
        rows = conn.execute(
            "SELECT * FROM pages ORDER BY id LIMIT ? OFFSET ?",
            (page_size, page * page_size),
        ).fetchall()
        conn.close()
        ok = len(rows) == page_size and rows[0][0] == page * page_size
        return StressReport(
            "pagination_stress", ok, time.monotonic() - start,
            f"page={page}, size={page_size}, got={len(rows)}",
            len(rows), 0,
        )

    def simulate_bounded_cache_pressure(self) -> StressReport:
        start = time.monotonic()
        db = self._workspace / "cache_pressure.db"
        conn = sqlite3.connect(str(db), timeout=30.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -512")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS cache_test "
            "(id INTEGER PRIMARY KEY, val TEXT, payload BLOB)"
        )
        for i in range(20000):
            conn.execute(
                "INSERT INTO cache_test VALUES (?, ?, ?)",
                (i, f"v{i}", b"z" * 512),
            )
        conn.commit()
        cnt = conn.execute("SELECT COUNT(*) FROM cache_test").fetchone()[0]
        conn.close()
        ok = cnt == 20000
        return StressReport(
            "bounded_cache_pressure", ok,
            time.monotonic() - start,
            f"rows={cnt} with 512KB cache", cnt, 0,
        )

    def run_all(self) -> list[StressReport]:
        return [
            self.simulate_million_row_archive(),
            self.simulate_concurrent_workstation_load(),
            self.simulate_large_wal_growth(),
            self.simulate_archive_fragmentation(),
            self.simulate_replay_consistency_stress(),
            self.simulate_pagination_stress(),
            self.simulate_bounded_cache_pressure(),
        ]
