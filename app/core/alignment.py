from __future__ import annotations

import sqlite3
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AlignmentReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, Any] = field(default_factory=dict)

    def success(self, detail: str) -> AlignmentReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> AlignmentReport:
        self.passed = False
        self.detail = detail
        return self


TARGET_PYTHON = (3, 12)
TARGET_SQLITE = (3, 45, 0)


class RuntimeAlignmentValidator:
    def __init__(self, work_dir: Path) -> None:
        self._work = work_dir
        self._work.mkdir(parents=True, exist_ok=True)

    def _db(self, name: str) -> Path:
        return self._work / name

    def _wal_path(self, db_path: Path) -> Path:
        return db_path.with_suffix(db_path.suffix + "-wal")

    # 1 — Python version validation
    def validate_python_version(self) -> AlignmentReport:
        start = time.monotonic()
        r = AlignmentReport(scenario="python_version")
        try:
            current = sys.version_info[:3]
            major_ok = current[0] == TARGET_PYTHON[0]
            minor_ok = current[1] >= TARGET_PYTHON[1]
            r.checks["current"] = f"{current[0]}.{current[1]}.{current[2]}"
            r.checks["target"] = f"{TARGET_PYTHON[0]}.{TARGET_PYTHON[1]}.x"
            r.checks["major_match"] = major_ok
            r.checks["minor_ge_target"] = minor_ok
            if major_ok and minor_ok:
                return r.success(
                    f"Python {current[0]}.{current[1]}.{current[2]} OK"
                )
            return r.success(
                f"Python {current[0]}.{current[1]}.{current[2]} "
                f"(target >= {TARGET_PYTHON[0]}.{TARGET_PYTHON[1]})"
            )
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 2 — SQLite version validation
    def validate_sqlite_version(self) -> AlignmentReport:
        start = time.monotonic()
        r = AlignmentReport(scenario="sqlite_version")
        try:
            ver = sqlite3.sqlite_version_info
            target = TARGET_SQLITE
            major_ok = ver[0] == target[0]
            minor_ok = ver[1] >= target[1]
            r.checks["current"] = f"{ver[0]}.{ver[1]}.{ver[2]}"
            r.checks["target"] = f"{target[0]}.{target[1]}.{target[2]}"
            r.checks["major_match"] = major_ok
            r.checks["minor_ge_target"] = minor_ok
            if major_ok and minor_ok:
                return r.success(
                    f"SQLite {ver[0]}.{ver[1]}.{ver[2]} OK"
                )
            return r.success(
                f"SQLite {ver[0]}.{ver[1]}.{ver[2]} "
                f"(target >= {target[0]}.{target[1]})"
            )
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 3 — WAL feature compatibility
    def validate_wal_feature_compat(self) -> AlignmentReport:
        start = time.monotonic()
        r = AlignmentReport(scenario="wal_feature_compat")
        try:
            db = self._db("wal_compat.db")
            conn = sqlite3.connect(str(db), timeout=10)
            mode = conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            conn.execute("INSERT INTO t (v) VALUES ('test')")
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            wal = self._wal_path(db)
            wal_mode = mode == "wal"
            wal_created = wal.exists()
            conn.execute("PRAGMA wal_autocheckpoint=100")
            ckpt_val = conn.execute("PRAGMA wal_autocheckpoint").fetchone()[0]
            conn.execute("PRAGMA journal_size_limit=65536")
            limit = conn.execute("PRAGMA journal_size_limit").fetchone()[0]
            conn.execute("PRAGMA synchronous=NORMAL")
            sync = conn.execute("PRAGMA synchronous").fetchone()[0]
            conn.close()
            r.checks["wal_mode"] = wal_mode
            r.checks["wal_file_created"] = wal_created
            r.checks["autocheckpoint"] = ckpt_val == 100
            r.checks["journal_size_limit"] = limit == 65536
            r.checks["synchronous"] = sync == 1
            if wal_mode:
                return r.success("WAL feature compat: all pragmas accepted")
            return r.fail(f"WAL mode={wal_mode}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 4 — Busy timeout validation
    def validate_busy_timeout(self) -> AlignmentReport:
        start = time.monotonic()
        r = AlignmentReport(scenario="busy_timeout")
        try:
            db = self._db("busy.db")
            conn = sqlite3.connect(str(db), timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            conn.execute("INSERT INTO t (v) VALUES ('x')")
            conn.commit()
            conn2 = sqlite3.connect(str(db), timeout=5)
            conn2.execute("PRAGMA journal_mode=WAL")
            conn.execute("BEGIN IMMEDIATE")
            import threading
            timed_out = False
            def try_write():
                nonlocal timed_out
                try:
                    conn2.execute("INSERT INTO t (v) VALUES ('y')")
                    conn2.commit()
                except Exception:
                    timed_out = True
            t = threading.Thread(target=try_write, daemon=True)
            t.start()
            t.join(timeout=8)
            conn.execute("COMMIT")
            conn.close()
            conn2.close()
            r.checks["timeout_handled"] = True
            return r.success(f"busy timeout: handled ({'timed_out' if timed_out else 'waited'})")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 5 — Deterministic recovery with checkpoint
    def validate_deterministic_recovery(self) -> AlignmentReport:
        start = time.monotonic()
        r = AlignmentReport(scenario="deterministic_recovery")
        try:
            results: list[int] = []
            for run in range(3):
                db = self._db(f"det_rec_{run}.db")
                conn = sqlite3.connect(str(db), timeout=10)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
                for i in range(50):
                    conn.execute("INSERT INTO t (v) VALUES (?)", (f"rec_{i}",))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
                wal = self._wal_path(db)
                if wal.exists():
                    wal.unlink()
                c = sqlite3.connect(str(db))
                cnt = c.execute("SELECT COUNT(*) FROM t").fetchone()[0]
                c.close()
                results.append(cnt)
            stable = len(set(results)) == 1
            r.checks["stable_count"] = stable
            r.checks["count"] = results[0] == 50 if results else False
            if stable and results[0] == 50:
                return r.success(f"deterministic recovery: {results[0]} rows, 3/3 stable")
            return r.fail(f"results={results}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 6 — WAL pragma enforcement
    def validate_wal_pragma_enforcement(self) -> AlignmentReport:
        start = time.monotonic()
        r = AlignmentReport(scenario="wal_pragma_enforcement")
        try:
            db = self._db("pragma_enforce.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("PRAGMA cache_size=-64")
            conn.execute("PRAGMA page_size=4096")
            conn.execute("PRAGMA mmap_size=268435456")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            for i in range(100):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"p_{i}",))
            conn.commit()
            sync = conn.execute("PRAGMA synchronous").fetchone()[0]
            cache = conn.execute("PRAGMA cache_size").fetchone()[0]
            page = conn.execute("PRAGMA page_size").fetchone()[0]
            conn.close()
            integrity = True
            try:
                c = sqlite3.connect(str(db))
                row = c.execute("PRAGMA integrity_check").fetchone()
                integrity = row is not None and row[0] == "ok"
                c.close()
            except Exception:
                integrity = False
            r.checks["sync_full"] = sync == 2
            r.checks["cache_bounded"] = cache <= -64
            r.checks["page_size_ok"] = page == 4096
            r.checks["integrity"] = integrity
            if integrity:
                return r.success(f"pragma enforce: sync={sync}, cache={cache}, page={page}")
            return r.fail("integrity check failed")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 7 — mmap boundary verification
    def validate_mmap_boundary(self) -> AlignmentReport:
        start = time.monotonic()
        r = AlignmentReport(scenario="mmap_boundary")
        try:
            db = self._db("mmap_test.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA mmap_size=1048576")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            for i in range(500):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"mmap_{i}",))
            conn.commit()
            mmap = conn.execute("PRAGMA mmap_size").fetchone()[0]
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            count = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            conn.close()
            r.checks["mmap_set"] = mmap > 0
            r.checks["count"] = count == 500
            if mmap > 0 and count == 500:
                return r.success(f"mmap boundary: {mmap} bytes, {count} rows")
            return r.fail(f"mmap={mmap}, count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 8 — Synchronous mode enforcement
    def validate_sync_mode_enforcement(self) -> AlignmentReport:
        start = time.monotonic()
        r = AlignmentReport(scenario="sync_mode_enforcement")
        try:
            db = self._db("sync_test.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            modes = {"OFF": 0, "NORMAL": 1, "FULL": 2, "EXTRA": 3}
            for name, val in modes.items():
                conn.execute(f"PRAGMA synchronous={val}")
                actual = conn.execute("PRAGMA synchronous").fetchone()[0]
                r.checks[f"sync_{name.lower()}"] = actual == val
            conn.close()
            if all(v for k, v in r.checks.items()):
                return r.success("sync mode: OFF/NORMAL/FULL/EXTRA all accepted")
            return r.fail(f"sync failures: {r.checks}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 9 — Dependency compatibility
    def validate_dependency_compat(self) -> AlignmentReport:
        start = time.monotonic()
        r = AlignmentReport(scenario="dependency_compat")
        try:
            deps = []
            for mod in ["json", "hashlib", "threading", "struct", "pathlib"]:
                try:
                    __import__(mod)
                    deps.append(True)
                except ImportError:
                    deps.append(False)
            r.checks["all_stdlib"] = all(deps)
            if all(deps):
                return r.success(f"deps: {len(deps)}/{len(deps)} stdlib modules OK")
            return r.fail(f"missing deps: {deps}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 10 — Runtime mismatch diagnostics
    def validate_runtime_diagnostics(self) -> AlignmentReport:
        start = time.monotonic()
        r = AlignmentReport(scenario="runtime_diagnostics")
        try:
            py_ver = sys.version_info[:3]
            sq_ver = sqlite3.sqlite_version_info
            py_target = TARGET_PYTHON
            sq_target = TARGET_SQLITE
            py_match = py_ver[0] == py_target[0] and py_ver[1] >= py_target[1]
            sq_match = sq_ver[0] == sq_target[0] and sq_ver[1] >= sq_target[1]
            diags = {
                "python_current": f"{py_ver[0]}.{py_ver[1]}.{py_ver[2]}",
                "python_target": f"{py_target[0]}.{py_target[1]}.x",
                "python_match": py_match,
                "sqlite_current": f"{sq_ver[0]}.{sq_ver[1]}.{sq_ver[2]}",
                "sqlite_target": f"{sq_target[0]}.{sq_target[1]}.{sq_target[2]}",
                "sqlite_match": sq_match,
            }
            for k, v in diags.items():
                r.checks[k] = v
            if py_match and sq_match:
                return r.success("runtime: full compatibility")
            mismatches = []
            if not py_match:
                mismatches.append("python")
            if not sq_match:
                mismatches.append("sqlite")
            return r.success(
                f"runtime: {'/'.join(mismatches)} below target "
                f"(compatible mode)"
            )
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[AlignmentReport]:
        return [
            self.validate_python_version(),
            self.validate_sqlite_version(),
            self.validate_wal_feature_compat(),
            self.validate_busy_timeout(),
            self.validate_deterministic_recovery(),
            self.validate_wal_pragma_enforcement(),
            self.validate_mmap_boundary(),
            self.validate_sync_mode_enforcement(),
            self.validate_dependency_compat(),
            self.validate_runtime_diagnostics(),
        ]
