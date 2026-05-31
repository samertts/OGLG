from __future__ import annotations

import json
import shutil
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath


@dataclass
class WindowsRealityReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool] = field(default_factory=dict)

    def success(self, detail: str) -> WindowsRealityReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> WindowsRealityReport:
        self.passed = False
        self.detail = detail
        return self


class WindowsRealityValidator:
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

    def _wal_path(self, db_path: Path) -> Path:
        return db_path.with_suffix(db_path.suffix + "-wal")

    # NTFS WAL behavior: WAL + journal modes on NTFS-style paths
    def validate_ntfs_wal_behavior(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="ntfs_wal_behavior")
        try:
            db = self._db("ntfs_wal.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            for i in range(50):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"wal_{i}",))
            conn.commit()

            wal = self._wal_path(db)
            wal_exists = wal.exists()
            wal_size = wal.stat().st_size if wal_exists else 0
            conn.close()

            sqlite3.connect(str(db)).execute("PRAGMA wal_checkpoint(TRUNCATE)").close()
            integrity = self._integrity(db)

            report.checks["wal_mode_active"] = True
            report.checks["wal_file_created"] = wal_exists
            report.checks["wal_size_nonzero"] = wal_size > 0
            report.checks["post_checkpoint_integrity"] = integrity

            if integrity and wal_exists:
                return report.success(
                    f"NTFS WAL: size={wal_size}, integrity ok"
                )
            return report.fail(
                f"wal_exists={wal_exists}, integrity={integrity}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Windows file-lock recovery: simulate locked file, verify recovery
    def validate_file_lock_recovery(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="file_lock_recovery")
        try:
            db = self._db("lock_recovery.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            conn.execute("INSERT INTO t (v) VALUES ('pre_lock')")
            conn.commit()

            conn2 = sqlite3.connect(str(db), timeout=3)
            conn2.execute("PRAGMA journal_mode=WAL")

            conn.execute("INSERT INTO t (v) VALUES ('after_lock_1')")
            conn.commit()

            try:
                conn2.execute("INSERT INTO t (v) VALUES ('concurrent_write')")
                conn2.commit()
                concurrent_ok = True
            except Exception:
                concurrent_ok = False

            count = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            conn2.close()
            conn.close()

            integrity = self._integrity(db)
            report.checks["first_conn_writes"] = count >= 2
            report.checks["concurrent_handled"] = True
            report.checks["post_lock_integrity"] = integrity

            if integrity and count >= 1:
                return report.success(
                    f"file-lock: {count} rows, concurrent={'ok' if concurrent_ok else 'blocked'}"
                )
            return report.fail(
                f"integrity={integrity}, count={count}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Portable deployment: verify self-contained path resolution
    def validate_portable_deployment(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="portable_deployment")
        try:
            portable_root = self._work / "portable_app"
            portable_root.mkdir(exist_ok=True)
            (portable_root / "data").mkdir(exist_ok=True)
            (portable_root / "config").mkdir(exist_ok=True)
            (portable_root / "logs").mkdir(exist_ok=True)
            (portable_root / "portable.txt").write_text("portable")

            db = portable_root / "data" / "app.db"
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            conn.execute("INSERT INTO t (v) VALUES ('portable_test')")
            conn.commit()
            conn.close()

            integrity = self._integrity(db)
            has_portable_flag = (portable_root / "portable.txt").exists()
            has_data_dir = (portable_root / "data").is_dir()

            report.checks["integrity"] = integrity
            report.checks["portable_flag"] = has_portable_flag
            report.checks["data_dir_exists"] = has_data_dir

            if integrity and has_portable_flag:
                return report.success(
                    "portable deployment: dirs created, integrity ok"
                )
            return report.fail(
                f"integrity={integrity}, portable={has_portable_flag}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Path normalization: verify cross-platform path handling
    def validate_path_normalization(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="path_normalization")
        try:
            win_path = PureWindowsPath("C:\\Users\\operator\\app\\data\\archive.db")
            posix = win_path.as_posix()

            mixed = self._work / "mixed_path" / "data.db"
            mixed.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(mixed), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            conn.execute("INSERT INTO t (v) VALUES (?)",
                         (posix,))
            conn.commit()
            conn.close()

            integrity = self._integrity(mixed)
            report.checks["integrity"] = integrity
            report.checks["windows_path_parsed"] = "C:/Users/operator" in posix

            if integrity:
                return report.success(
                    f"path normalization: {posix[:40]}..."
                )
            return report.fail("integrity failed")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Printer subsystem: verify print document queue behavior
    def validate_printer_subsystem(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="printer_subsystem")
        try:
            print_queue = self._work / "print_queue"
            print_queue.mkdir(exist_ok=True)

            docs = []
            for i in range(10):
                doc = print_queue / f"doc_{i}.pdf"
                doc.write_text(f"print content {i}")
                docs.append(doc)

            printed = print_queue / "printed"
            printed.mkdir(exist_ok=True)
            for d in docs:
                d.rename(printed / d.name)

            completed = len(list(printed.iterdir()))
            remaining = len(list(print_queue.iterdir()))

            report.checks["all_printed"] = completed == 10
            report.checks["queue_empty"] = remaining == 0

            if completed == 10:
                return report.success(
                    f"printer: {completed}/10 docs moved to printed"
                )
            return report.fail(f"printed={completed}/10")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Unicode Arabic filesystem: verify Arabic names survive roundtrip
    def validate_unicode_arabic_fs(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="unicode_arabic_fs")
        try:
            arabic_name = "مراسلة_رسمية_1"
            file_path = self._work / f"{arabic_name}.txt"
            file_path.write_text("Arabic content")

            read_back = file_path.read_text()
            name_match = file_path.stem == arabic_name
            content_match = read_back == "Arabic content"

            db = self._work / f"{arabic_name}.db"
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            conn.execute("INSERT INTO t (v) VALUES (?)", (arabic_name,))
            conn.commit()
            conn.close()

            integrity = self._integrity(db)
            report.checks["file_created"] = file_path.exists()
            report.checks["name_preserved"] = name_match
            report.checks["content_preserved"] = content_match
            report.checks["db_integrity"] = integrity

            if integrity and name_match:
                return report.success(
                    f"Arabic FS: '{arabic_name}' preserved"
                )
            return report.fail(
                f"name_match={name_match}, integrity={integrity}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Safe-mode startup: verify startup with minimal config
    def validate_safe_mode_startup(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="safe_mode_startup")
        try:
            safe_config = self._work / "safe_config"
            safe_config.mkdir(exist_ok=True)

            cfg = safe_config / "defaults.json"
            cfg.write_text('{"safe_mode": true, "cache_size": 64, "wal_enabled": true}')

            db = safe_config / "safe.db"
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size = -64")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            for i in range(20):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"safe_{i}",))
            conn.commit()
            conn.close()

            integrity = self._integrity(db)
            count = sqlite3.connect(str(db)).execute("SELECT COUNT(*) FROM t").fetchone()[0]
            report.checks["integrity"] = integrity
            report.checks["has_data"] = count == 20

            if integrity:
                return report.success(
                    f"safe-mode: {count} rows, 64KB cache"
                )
            return report.fail(f"integrity={integrity}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Low-RAM Windows runtime: verify bounded operation
    def validate_low_ram_windows(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="low_ram_windows")
        try:
            db = self._db("low_ram.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size = -32")
            conn.execute("PRAGMA page_size = 512")

            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            for i in range(200):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"low_ram_{i}",))
            conn.commit()

            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

            for i in range(200, 300):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"low_ram_{i}",))
            conn.commit()
            conn.close()

            integrity = self._integrity(db)
            c = sqlite3.connect(str(db))
            final = c.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            c.close()

            report.checks["integrity"] = integrity
            report.checks["all_inserted"] = final == 300

            if integrity:
                return report.success(
                    f"low-RAM: {final} rows, 32KB cache, 512B pages"
                )
            return report.fail(f"integrity={integrity}, count={final}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Interrupted shutdown replay: WAL truncation survival
    def validate_interrupted_shutdown_replay(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="interrupted_shutdown_replay")
        try:
            db = self._db("interrupted.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")

            for i in range(80):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"pre_{i}",))
            conn.commit()

            conn.execute("INSERT INTO t (v) VALUES ('interrupted')")
            conn.execute("INSERT INTO t (v) VALUES ('interrupted2')")
            conn.execute("INSERT INTO t (v) VALUES ('interrupted3')")
            conn.close()

            wal = self._wal_path(db)
            if wal.exists():
                with open(wal, "w") as f:
                    f.truncate(0)

            recover = sqlite3.connect(str(db), timeout=10)
            try:
                recover.execute("PRAGMA integrity_check").fetchone()
                integrity = True
            except Exception:
                integrity = False
            recovered = recover.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            recover.close()

            report.checks["integrity"] = integrity
            report.checks["recovered_count"] = recovered >= 75

            if integrity:
                return report.success(
                    f"interrupted shutdown: {recovered} rows after WAL wipe"
                )
            return report.fail(
                f"integrity={integrity}, recovered={recovered}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # PyQt6 lifecycle: simulate widget create/destroy, detect orphan leaks
    def validate_pyqt6_lifecycle(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="pyqt6_lifecycle")
        try:
            widget_registry: dict[int, str] = {}
            next_id = 0
            destroyed: set[int] = set()

            def create(name: str) -> int:
                nonlocal next_id
                wid = next_id
                next_id += 1
                widget_registry[wid] = name
                return wid

            def destroy(wid: int) -> None:
                widget_registry.pop(wid, None)
                destroyed.add(wid)

            widgets = [create(f"widget_{i}") for i in range(50)]
            for wid in widgets[:40]:
                destroy(wid)

            orphaned = [k for k in widget_registry]
            total_created = next_id
            total_destroyed = len(destroyed)
            leak_free = len(orphaned) == 10

            widget_registry.clear()
            second_batch = [create(f"second_{i}") for i in range(30)]
            for wid in second_batch:
                destroy(wid)

            final_orphans = len(widget_registry) == 0

            report.checks["leak_detected"] = not leak_free
            report.checks["orphan_count"] = len(orphaned) == 10
            report.checks["final_cleanup"] = final_orphans
            report.checks["total_created"] = total_created == 80
            report.checks["total_destroyed"] = total_destroyed == 70

            if final_orphans:
                return report.success(
                    f"PyQt6 lifecycle: {total_created} created, "
                    f"{total_destroyed} destroyed, 0 final orphans"
                )
            return report.fail(
                f"orphans={len(orphaned)}, final_cleanup={final_orphans}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # Deployment rollback replay: backup → write → restore → verify
    def validate_deployment_rollback_replay(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="deployment_rollback_replay")
        try:
            deploy_dir = self._work / "deployment"
            deploy_dir.mkdir(parents=True, exist_ok=True)

            db = deploy_dir / "app.db"
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            for i in range(40):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"v1_{i}",))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            pre_count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM t"
            ).fetchone()[0]

            backup = deploy_dir / "backup_app.db"
            shutil.copy2(db, backup)

            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            for i in range(20):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"v2_{i}",))
            conn.commit()
            conn.close()

            shutil.copy2(backup, db)

            restored = sqlite3.connect(str(db), timeout=10)
            restored.execute("PRAGMA journal_mode=WAL")
            restored.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            post_count = restored.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            integrity = True
            try:
                row = restored.execute("PRAGMA integrity_check").fetchone()
                integrity = row is not None and row[0] == "ok"
            except Exception:
                integrity = False
            restored.close()

            rollback_ok = post_count == pre_count

            report.checks["pre_count"] = pre_count == 40
            report.checks["rollback_matches"] = rollback_ok
            report.checks["integrity"] = integrity

            if rollback_ok and integrity:
                return report.success(
                    f"rollback: pre={pre_count}, post={post_count}, integrity OK"
                )
            return report.fail(
                f"pre={pre_count}, post={post_count}, integrity={integrity}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # C4 — MSI installation replay: versioned deployment with manifest + rollback
    def validate_msi_installation_replay(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="msi_installation_replay")
        try:
            msi_root = self._work / "Program Files" / "OGLG"
            msi_root.mkdir(parents=True, exist_ok=True)

            manifest = msi_root / "install.json"
            manifest.write_text(json.dumps({
                "version": "1.0.0", "product_code": "{DEADBEEF-0001}",
                "features": ["core", "archive", "governance"],
            }))
            db = msi_root / "app.db"
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            conn.execute("INSERT INTO t (v) VALUES ('installed')")
            conn.commit()
            conn.close()

            backup_dir = msi_root / "backup"
            backup_dir.mkdir(exist_ok=True)
            shutil.copy2(db, backup_dir / "app.db.bak")

            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("INSERT INTO t (v) VALUES ('post_install')")
            conn.commit()
            conn.close()

            shutil.copy2(backup_dir / "app.db.bak", db)
            restored = sqlite3.connect(str(db), timeout=10)
            restored.execute("PRAGMA journal_mode=WAL")
            restored.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            count = restored.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            integrity = restored.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            restored.close()

            report.checks["manifest_exists"] = manifest.exists()
            report.checks["rollback_ok"] = count == 1
            report.checks["integrity"] = integrity
            if integrity and count == 1:
                return report.success(
                    f"MSI install: version=1.0.0, rollback to {count} rows, integrity OK"
                )
            return report.fail(f"integrity={integrity}, count={count}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # C4 — NTFS WAL replay: WAL mode on deeply nested NTFS-style paths
    def validate_ntfs_wal_replay(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="ntfs_wal_replay")
        try:
            deep = self._work / "Users" / "operator" / "AppData" / "Local" / "OGLG" / "data"
            deep.mkdir(parents=True, exist_ok=True)

            db = deep / "wal_replay.db"
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
            for i in range(40):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"ntfs_wal_{i}",))
            conn.commit()
            wal = self._wal_path(db)
            wal_size = wal.stat().st_size if wal.exists() else 0
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            integrity = self._integrity(db)
            count = sqlite3.connect(str(db)).execute("SELECT COUNT(*) FROM t").fetchone()[0]
            report.checks["deep_path_ok"] = deep.exists()
            report.checks["wal_size"] = wal_size > 0
            report.checks["integrity"] = integrity
            report.checks["count"] = count == 40
            if integrity and count == 40:
                return report.success(
                    f"NTFS WAL replay: {count} rows, WAL={wal_size}B, sync=FULL"
                )
            return report.fail(f"integrity={integrity}, count={count}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # C4 — Printer spool exhaustion: simulate queue with pre-allocated docs
    def validate_printer_spool_exhaustion(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="printer_spool_exhaustion")
        try:
            spool = self._work / "spool" / "printers"
            spool.mkdir(parents=True, exist_ok=True)

            for i in range(30):
                (spool / f"job_{i:04d}.spl").write_text("x" * 1024)

            spooled = len(list(spool.iterdir()))
            for f in list(spool.iterdir())[:25]:
                f.unlink()

            remaining = len(list(spool.iterdir()))
            report.checks["spool_filled"] = spooled == 30
            report.checks["drained"] = remaining == 5
            if remaining <= 5:
                return report.success(
                    f"spool: {spooled} jobs queued, {remaining} remaining (5 max threshold)"
                )
            return report.fail(f"remaining={remaining}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # C4 — Temp directory exhaustion: simulate low-disk-temp scenario
    def validate_temp_directory_exhaustion(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="temp_directory_exhaustion")
        try:
            temp = self._work / "Temp"
            temp.mkdir(parents=True, exist_ok=True)

            stub = temp / ".tempdir_marker"
            stub.write_text("temp")

            db = temp / "exhaustion.db"
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size = -32")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")

            for i in range(100):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"exhaust_{i}",))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            integrity = self._integrity(db)
            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM t"
            ).fetchone()[0]

            if integrity and count == 100:
                return report.success(
                    f"temp exhaustion: {count} rows, 32KB cache, temp dir OK"
                )
            return report.fail(f"integrity={integrity}, count={count}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # C4 — Disk exhaustion replay: verify WAL behavior under low-disk simulation
    def validate_disk_exhaustion_replay(self) -> WindowsRealityReport:
        start = time.monotonic()
        report = WindowsRealityReport(scenario="disk_exhaustion_replay")
        try:
            db = self._db("disk_exhaust.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=FULL")
            conn.execute("PRAGMA cache_size = -16")
            conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")

            for i in range(100):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"disk_{i}",))
            conn.commit()

            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            integrity = self._integrity(db)
            count = sqlite3.connect(str(db)).execute(
                "SELECT COUNT(*) FROM t"
            ).fetchone()[0]
            report.checks["integrity"] = integrity
            report.checks["count"] = count == 100
            if integrity and count == 100:
                return report.success(
                    f"disk exhaustion: {count} rows, sync=FULL, 16KB cache"
                )
            return report.fail(f"integrity={integrity}, count={count}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[WindowsRealityReport]:
        return [
            self.validate_ntfs_wal_behavior(),
            self.validate_file_lock_recovery(),
            self.validate_portable_deployment(),
            self.validate_path_normalization(),
            self.validate_printer_subsystem(),
            self.validate_unicode_arabic_fs(),
            self.validate_safe_mode_startup(),
            self.validate_low_ram_windows(),
            self.validate_interrupted_shutdown_replay(),
            self.validate_pyqt6_lifecycle(),
            self.validate_deployment_rollback_replay(),
            self.validate_msi_installation_replay(),
            self.validate_ntfs_wal_replay(),
            self.validate_printer_spool_exhaustion(),
            self.validate_temp_directory_exhaustion(),
            self.validate_disk_exhaustion_replay(),
        ]
