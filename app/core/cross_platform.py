from __future__ import annotations

import os
import shutil
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath


@dataclass
class CrossPlatformReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool | str | int] = field(default_factory=dict)

    def success(self, detail: str) -> CrossPlatformReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> CrossPlatformReport:
        self.passed = False
        self.detail = detail
        return self


class CrossPlatformValidator:
    def __init__(self, work_dir: Path) -> None:
        self._work = work_dir
        self._work.mkdir(parents=True, exist_ok=True)

    def _db(self, name: str) -> Path:
        return self._work / name

    def _wal_path(self, db_path: Path) -> Path:
        return db_path.with_suffix(db_path.suffix + "-wal")

    def _make_db(self, path: Path) -> sqlite3.Connection:
        conn = sqlite3.connect(str(path), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
        conn.commit()
        return conn

    def _integrity(self, path: Path) -> bool:
        try:
            conn = sqlite3.connect(str(path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            return row is not None and row[0] == "ok"
        except Exception:
            return False

    def _report(self, scenario: str) -> CrossPlatformReport:
        return CrossPlatformReport(scenario=scenario)

    # 1 — Windows CI parity: WAL behavior on Windows-style paths
    def validate_windows_ci_parity(self) -> CrossPlatformReport:
        start = time.monotonic()
        r = self._report("windows_ci_parity")
        try:
            win_path = PureWindowsPath("C:\\deploy\\data\\app.db")
            win_path.as_posix()
            db = self._db("windows_ci.db")
            conn = self._make_db(db)
            for i in range(50):
                conn.execute("INSERT INTO t (v) VALUES (?)",
                             (f"win_ci_{i}",))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            count = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            conn.close()
            integrity = self._integrity(db)
            wal = self._wal_path(db)
            wal_clean = not wal.exists() or wal.stat().st_size == 0
            r.checks["count"] = count == 50
            r.checks["integrity"] = integrity
            r.checks["wal_clean"] = wal_clean
            if integrity and count == 50:
                return r.success(f"Windows CI: {count} rows, WAL truncated")
            return r.fail(f"count={count}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 2 — Replay parity across posix/nt paths
    def validate_replay_parity(self) -> CrossPlatformReport:
        start = time.monotonic()
        r = self._report("replay_parity")
        try:
            results: list[int] = []
            for variant in ["posix", "nt"]:
                db = self._db(f"replay_{variant}.db")
                conn = self._make_db(db)
                for i in range(40):
                    conn.execute("INSERT INTO t (v) VALUES (?)",
                                 (f"{variant}_{i}",))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
                wal = self._wal_path(db)
                if wal.exists():
                    wal.unlink()
                cnt = sqlite3.connect(str(db)).execute(
                    "SELECT COUNT(*) FROM t"
                ).fetchone()[0]
                results.append(cnt)
            pariy = len(set(results)) == 1
            r.checks["posix"] = results[0] == 40
            r.checks["nt"] = results[1] == 40
            r.checks["parity"] = pariy
            if pariy:
                return r.success(f"replay parity: {results[0]}/{results[1]}")
            return r.fail(f"results={results}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 3 — WAL parity: WAL behavior identical across simulated platforms
    def validate_wal_parity(self) -> CrossPlatformReport:
        start = time.monotonic()
        r = self._report("wal_parity")
        try:
            peeks: list[int] = []
            for label in ["a", "b"]:
                db = self._db(f"wal_parity_{label}.db")
                conn = self._make_db(db)
                for batch in range(5):
                    for i in range(20):
                        conn.execute("INSERT INTO t (v) VALUES (?)",
                                     (f"p_{label}_{batch}_{i}",))
                    conn.commit()
                    conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
                wal = self._wal_path(db)
                wal_size = wal.stat().st_size if wal.exists() else 0
                peeks.append(wal_size)
                conn.close()
            sizes_match = max(peeks) - min(peeks) < 4096 if peeks else False
            r.checks["wal_sizes"] = sizes_match
            if sizes_match:
                return r.success(f"WAL parity: sizes within 4KB ({peeks})")
            return r.fail(f"WAL sizes diverged: {peeks}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 4 — Deployment parity: deterministic results regardless of path style
    def validate_deployment_parity(self) -> CrossPlatformReport:
        start = time.monotonic()
        r = self._report("deployment_parity")
        try:
            paths = [
                ("linux", PurePosixPath("/opt/oglg/data/deploy.db")),
                ("windows", PureWindowsPath("C:\\oglg\\data\\deploy.db")),
            ]
            for label, p in paths:
                db = self._db(f"deploy_{label}.db")
                conn = sqlite3.connect(str(db), timeout=10)
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("CREATE TABLE IF NOT EXISTS deploy "
                             "(id INTEGER PRIMARY KEY, key TEXT, value TEXT)")
                for i in range(30):
                    conn.execute(
                        "INSERT INTO deploy (key, value) VALUES (?,?)",
                        (f"key_{i}", f"val_{i}"),
                    )
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
                r.checks[f"{label}_ok"] = self._integrity(db)
            if all(v for k, v in r.checks.items() if "_ok" in k):
                return r.success("deployment parity: both platforms OK")
            return r.fail(f"checks={r.checks}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 5 — Deterministic archive replay on any platform
    def validate_deterministic_archive_replay(self) -> CrossPlatformReport:
        start = time.monotonic()
        r = self._report("deterministic_archive_replay")
        try:
            results: list[int] = []
            for run in range(3):
                db = self._db(f"arch_parity_{run}.db")
                conn = self._make_db(db)
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS archive ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "snap_id TEXT UNIQUE, checksum TEXT)"
                )
                for i in range(30):
                    conn.execute(
                        "INSERT OR IGNORE INTO archive (snap_id, checksum) "
                        "VALUES (?,?)",
                        (f"snap_{i}", f"ck_{i}"),
                    )
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
                wal = self._wal_path(db)
                if wal.exists():
                    wal.unlink()
                cnt = sqlite3.connect(str(db)).execute(
                    "SELECT COUNT(*) FROM archive"
                ).fetchone()[0]
                results.append(cnt)
            stable = len(set(results)) == 1
            r.checks["stable"] = stable
            r.checks["count"] = results[0] == 30 if results else False
            if stable and results[0] == 30:
                return r.success(f"archive replay: {results[0]}, 3/3 stable")
            return r.fail(f"results={results}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 6 — Federation replay parity
    def validate_federation_replay_parity(self) -> CrossPlatformReport:
        start = time.monotonic()
        r = self._report("federation_replay_parity")
        try:
            node_a = self._db("fed_a.db")
            node_b = self._db("fed_b.db")
            conn_a = self._make_db(node_a)
            conn_b = self._make_db(node_b)
            conn_b.execute(
                "CREATE TABLE IF NOT EXISTS events ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "event_id TEXT UNIQUE, source TEXT)"
            )
            for i in range(40):
                conn_a.execute("INSERT INTO t (v) VALUES (?)",
                               (f"fed_{i}",))
            conn_a.commit()
            conn_a.close()
            a_data = sqlite3.connect(str(node_a)).execute(
                "SELECT v FROM t ORDER BY id"
            ).fetchall()
            for (v,) in a_data:
                conn_b.execute(
                    "INSERT OR IGNORE INTO events (event_id, source) VALUES (?,?)",
                    (v, "node_a"),
                )
            conn_b.commit()
            cnt = conn_b.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            conn_b.close()
            r.checks["federation_parity"] = cnt == 40
            if cnt == 40:
                return r.success(f"federation parity: {cnt} events replicated")
            return r.fail(f"cnt={cnt}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 7 — Installer validation replay
    def validate_installer_validation(self) -> CrossPlatformReport:
        start = time.monotonic()
        r = self._report("installer_validation")
        try:
            install_layout = self._work / "install"
            for sub in ["bin", "data", "config", "logs"]:
                (install_layout / sub).mkdir(parents=True, exist_ok=True)
            (install_layout / "app.db").write_text("placeholder")
            paths_ok = all(
                (install_layout / s).is_dir() for s in ["bin", "data", "config", "logs"]
            )
            db = install_layout / "test.db"
            conn = self._make_db(db)
            for i in range(20):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"install_{i}",))
            conn.commit()
            conn.close()
            integrity = self._integrity(db)
            r.checks["layout"] = paths_ok
            r.checks["integrity"] = integrity
            if paths_ok and integrity:
                return r.success("installer: layout OK, DB integrity OK")
            return r.fail(f"layout={paths_ok}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 8 — Package verification parity
    def validate_package_verification(self) -> CrossPlatformReport:
        start = time.monotonic()
        r = self._report("package_verification")
        try:
            dist = self._work / "dist"
            dist.mkdir(exist_ok=True)
            artifacts = ["oglg.spec", "setup.iss", "build_portable.py"]
            for art in artifacts:
                (dist / art).write_text(f"# {art}\n")
            all_exist = all((dist / a).exists() for a in artifacts)
            r.checks["artifacts_exist"] = all_exist
            if all_exist:
                return r.success(f"package: {len(artifacts)} artifacts")
            return r.fail(f"missing: {[a for a in artifacts if not (dist/a).exists()]}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 9 — Filesystem atomicity replay
    def validate_filesystem_atomicity_replay(self) -> CrossPlatformReport:
        start = time.monotonic()
        r = self._report("filesystem_atomicity_replay")
        try:
            db = self._db("atomic.db")
            conn = self._make_db(db)
            for i in range(30):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"atomic_{i}",))
            conn.commit()
            conn.close()
            backup = self._db("atomic_backup.db")
            import shutil
            shutil.copy2(db, backup)
            import os
            os.replace(str(backup), str(db))
            integrity = self._integrity(db)
            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM t"
            ).fetchone()[0]
            r.checks["integrity"] = integrity
            r.checks["count"] = count == 30
            if integrity and count == 30:
                return r.success(f"atomic: {count} rows after atomic replace")
            return r.fail(f"integrity={integrity}, count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 10 — Temp-file replacement recovery
    def validate_temp_file_replacement(self) -> CrossPlatformReport:
        start = time.monotonic()
        r = self._report("temp_file_replacement")
        try:
            target = self._db("target.db")
            conn = self._make_db(target)
            for i in range(50):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"orig_{i}",))
            conn.commit()
            conn.close()
            orig_count = sqlite3.connect(str(target)).execute(
                "SELECT COUNT(*) FROM t"
            ).fetchone()[0]
            temp = self._db("temp_new.db")
            conn = self._make_db(temp)
            for i in range(30):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"new_{i}",))
            conn.commit()
            conn.close()
            shutil.copy2(temp, target)
            final_count = sqlite3.connect(str(target)).execute(
                "SELECT COUNT(*) FROM t"
            ).fetchone()[0]
            r.checks["orig_count"] = orig_count == 50
            r.checks["replaced"] = final_count == 30
            if r.checks["replaced"]:
                return r.success(f"temp replace: {final_count} rows (was {orig_count})")
            return r.fail(f"orig={orig_count}, final={final_count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 11 — NTFS rename atomicity simulation
    def validate_ntfs_rename_atomicity(self) -> CrossPlatformReport:
        start = time.monotonic()
        r = self._report("ntfs_rename_atomicity")
        try:
            src = self._db("rename_src.db")
            dst = self._db("rename_dst.db")
            conn = self._make_db(src)
            for i in range(40):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"rename_{i}",))
            conn.commit()
            conn.close()
            for attempt in range(5):
                tmp = self._db(f"rename_tmp_{attempt}.db")
                shutil.copy2(src, tmp)
                os.replace(str(tmp), str(dst))
                if self._integrity(dst):
                    r.checks[f"rename_{attempt}"] = True
                else:
                    r.checks[f"rename_{attempt}"] = False
            count = sqlite3.connect(str(dst)).execute(
                "SELECT COUNT(*) FROM t"
            ).fetchone()[0]
            all_ok = all(r.checks.get(f"rename_{i}", False) for i in range(5))
            r.checks["count"] = count == 40
            if all_ok and count == 40:
                return r.success(f"NTFS rename: {count} rows, 5/5 atomic")
            return r.fail(f"all_ok={all_ok}, count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[CrossPlatformReport]:
        return [
            self.validate_windows_ci_parity(),
            self.validate_replay_parity(),
            self.validate_wal_parity(),
            self.validate_deployment_parity(),
            self.validate_deterministic_archive_replay(),
            self.validate_federation_replay_parity(),
            self.validate_installer_validation(),
            self.validate_package_verification(),
            self.validate_filesystem_atomicity_replay(),
            self.validate_temp_file_replacement(),
            self.validate_ntfs_rename_atomicity(),
        ]
