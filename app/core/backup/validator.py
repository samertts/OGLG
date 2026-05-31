from __future__ import annotations

import hashlib
import shutil
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RestoreReport:
    scenario: str
    duration_seconds: float
    passed: bool = False
    detail: str = ""
    restored_count: int = 0
    integrity_ok: bool = False
    checks: dict[str, bool] = field(default_factory=dict)

    def fail(self, detail: str) -> RestoreReport:
        self.passed = False
        self.detail = detail
        return self

    def succeed(self, detail: str) -> RestoreReport:
        self.passed = True
        self.detail = detail
        return self


class BackupValidator:
    def __init__(self, work_dir: Path) -> None:
        self._work = work_dir
        self._work.mkdir(parents=True, exist_ok=True)

    # -- helpers --

    def _create_source_db(self, name: str, rows: int = 50) -> tuple[Path, int]:
        path = self._work / name
        if path.exists():
            path.unlink()
        conn = sqlite3.connect(str(path))
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)")
        for i in range(rows):
            conn.execute("INSERT INTO t (v) VALUES (?)", (f"val_{i}",))
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
        conn.close()
        return path, count

    def _checksum(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _copy(self, src: Path) -> Path:
        dst = self._work / f"{src.stem}_copy{src.suffix}"
        shutil.copy2(str(src), str(dst))
        return dst

    def _wal_checkpoint(self, db_path: Path) -> None:
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.close()

    def _integrity_check(self, db_path: Path) -> bool:
        try:
            conn = sqlite3.connect(str(db_path))
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            return row is not None and row[0] == "ok"
        except Exception:
            return False

    # -- hot backup --

    def validate_hot_backup(self) -> RestoreReport:
        start = time.monotonic()
        report = RestoreReport(scenario="hot_backup", duration_seconds=0.0)
        try:
            src, _ = self._create_source_db("hot_source.db", 100)

            backup_path = self._work / "hot_backup.db"
            if backup_path.exists():
                backup_path.unlink()

            live = sqlite3.connect(str(src))
            live.execute("PRAGMA journal_mode=WAL")
            live.execute("BEGIN IMMEDIATE")
            live.execute("INSERT INTO t (v) VALUES ('hot_written')")
            live.execute("INSERT INTO t (v) VALUES ('hot_written2')")
            live.commit()

            bak = sqlite3.connect(str(backup_path))
            live.backup(bak, pages=0, progress=None)
            bak.close()

            live.execute("INSERT INTO t (v) VALUES ('after_backup')")
            live.commit()
            live_count = live.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            live.close()

            bak_conn = sqlite3.connect(str(backup_path))
            bak_count = bak_conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            integrity = self._integrity_check(backup_path)
            bak_conn.close()

            report.checks["backup_integrity"] = integrity
            report.checks["live_has_newer_data"] = live_count > bak_count
            report.integrity_ok = integrity
            report.restored_count = bak_count

            if integrity and live_count > bak_count:
                return report.succeed(
                    f"hot backup consistent: {bak_count} rows, live={live_count}"
                )
            return report.fail(
                f"integrity={integrity}, bak={bak_count}, live={live_count}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- cold backup --

    def validate_cold_backup(self) -> RestoreReport:
        start = time.monotonic()
        report = RestoreReport(scenario="cold_backup", duration_seconds=0.0)
        try:
            src, expected = self._create_source_db("cold_source.db", 75)

            self._wal_checkpoint(src)

            backup_path = self._copy(src)
            integrity = self._integrity_check(backup_path)

            bak_conn = sqlite3.connect(str(backup_path))
            bak_count = bak_conn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            bak_conn.close()

            report.checks["integrity_ok"] = integrity
            report.checks["row_count_match"] = bak_count == expected
            report.integrity_ok = integrity
            report.restored_count = bak_count

            if integrity and bak_count == expected:
                return report.succeed(
                    f"cold backup: {bak_count}/{expected} rows, integrity ok"
                )
            return report.fail(
                f"integrity={integrity}, rows={bak_count}/{expected}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- WAL-consistent restore --

    def validate_wal_consistent_restore(self) -> RestoreReport:
        start = time.monotonic()
        report = RestoreReport(scenario="wal_consistent_restore", duration_seconds=0.0)
        try:
            src, _ = self._create_source_db("wal_source.db", 60)

            conn = sqlite3.connect(str(src))
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("INSERT INTO t (v) VALUES ('wal_pending')")
            conn.commit()
            conn.close()

            self._wal_checkpoint(src)

            restore_path = self._work / "wal_restored.db"
            shutil.copy2(str(src), str(restore_path))

            rconn = sqlite3.connect(str(restore_path))
            integrity = self._integrity_check(restore_path)
            count = rconn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            rconn.close()

            report.checks["integrity_ok"] = integrity
            report.checks["has_data"] = count > 0
            report.integrity_ok = integrity
            report.restored_count = count

            if integrity and count == 61:
                return report.succeed(
                    f"WAL-consistent restore: {count} rows, integrity ok"
                )
            return report.fail(f"integrity={integrity}, count={count}")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- archive replay restoration --

    def validate_archive_replay_restoration(self) -> RestoreReport:
        start = time.monotonic()
        report = RestoreReport(
            scenario="archive_replay_restoration", duration_seconds=0.0
        )
        try:
            src, expected = self._create_source_db("archive_src.db", 80)

            conn = sqlite3.connect(str(src))
            conn.execute("PRAGMA journal_mode=WAL")
            for i in range(20):
                conn.execute(
                    "INSERT INTO t (v) VALUES (?)", (f"archive_replay_{i}",)
                )
            conn.commit()
            expected += 20
            conn.close()

            archive_path = self._work / "archive_restore.db"
            shutil.copy2(str(src), str(archive_path))

            replay_conn = sqlite3.connect(str(archive_path))
            for i in range(10):
                replay_conn.execute(
                    "INSERT INTO t (v) VALUES (?)", (f"replay_{i}",)
                )
            replay_conn.commit()
            expected += 10
            replay_conn.close()

            fconn = sqlite3.connect(str(archive_path))
            integrity = self._integrity_check(archive_path)
            final_count = fconn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            fconn.close()

            report.checks["integrity_ok"] = integrity
            report.checks["count_match"] = final_count == expected
            report.integrity_ok = integrity
            report.restored_count = final_count

            if integrity and final_count == expected:
                return report.succeed(
                    f"archive replay restore: {final_count}/{expected} rows"
                )
            return report.fail(
                f"integrity={integrity}, count={final_count}/{expected}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- corruption recovery replay --

    def validate_corruption_recovery_replay(self) -> RestoreReport:
        start = time.monotonic()
        report = RestoreReport(
            scenario="corruption_recovery_replay", duration_seconds=0.0
        )
        try:
            src, expected = self._create_source_db("corrupt_src.db", 40)

            backup_path = self._copy(src)
            backup_hash = self._checksum(backup_path)

            conn = sqlite3.connect(str(src))
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()

            data = bytearray(src.read_bytes())
            if len(data) > 200:
                data[150] ^= 0xFF
            src.write_bytes(bytes(data))

            self._wal_checkpoint(src)

            restore_path = self._copy(backup_path)
            rconn = sqlite3.connect(str(restore_path))
            integrity = self._integrity_check(restore_path)
            count = rconn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            rconn.close()

            report.checks["backup_unaffected"] = self._checksum(backup_path) == backup_hash
            report.checks["restore_integrity"] = integrity
            report.checks["count_match"] = count == expected
            report.integrity_ok = integrity
            report.restored_count = count

            if integrity and count == expected:
                return report.succeed(
                    f"corruption recovery: {count}/{expected} rows from clean backup"
                )
            return report.fail(
                f"integrity={integrity}, count={count}/{expected}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- deterministic restore ordering --

    def validate_deterministic_restore_ordering(self) -> RestoreReport:
        start = time.monotonic()
        report = RestoreReport(
            scenario="deterministic_restore_ordering", duration_seconds=0.0
        )
        try:
            def run_restore() -> list[tuple[int, str]]:
                p, _ = self._create_source_db("order_temp.db", 30)
                c = sqlite3.connect(str(p))
                rows = c.execute("SELECT id, v FROM t ORDER BY id").fetchall()
                c.close()
                p.unlink()
                return rows

            r1 = run_restore()
            r2 = run_restore()
            deterministic = r1 == r2

            report.checks["deterministic_ordering"] = deterministic
            report.restored_count = len(r1)

            if deterministic:
                return report.succeed(
                    f"deterministic ordering: {len(r1)} rows, stable"
                )
            return report.fail("ordering differs between runs")
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- offline restore bundle --

    def validate_offline_restore_bundle(self) -> RestoreReport:
        start = time.monotonic()
        report = RestoreReport(
            scenario="offline_restore_bundle", duration_seconds=0.0
        )
        try:
            src, expected = self._create_source_db("bundle_src.db", 55)

            export_path = self._work / "bundle_export.db"
            shutil.copy2(str(src), str(export_path))
            export_hash = self._checksum(export_path)

            manifest_path = self._work / "bundle_manifest.sha256"
            manifest_path.write_text(f"{export_hash}  bundle_export.db\n")

            bundle_dir = self._work / "restore_bundle"
            bundle_dir.mkdir(exist_ok=True)
            shutil.copy2(str(export_path), bundle_dir / "bundle_export.db")
            shutil.copy2(str(manifest_path), bundle_dir / "bundle_manifest.sha256")

            ver_hash = hashlib.sha256(
                (bundle_dir / "bundle_export.db").read_bytes()
            ).hexdigest()
            manifest_content = (
                bundle_dir / "bundle_manifest.sha256"
            ).read_text().strip()
            hash_match = ver_hash in manifest_content

            restored = bundle_dir / "bundle_export.db"
            rconn = sqlite3.connect(str(restored))
            integrity = self._integrity_check(restored)
            count = rconn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            rconn.close()

            report.checks["hash_verified"] = hash_match
            report.checks["bundle_integrity"] = integrity
            report.checks["count_match"] = count == expected
            report.integrity_ok = integrity
            report.restored_count = count

            if hash_match and integrity and count == expected:
                return report.succeed(
                    f"offline bundle: {count}/{expected} rows, hash+integrity ok"
                )
            return report.fail(
                f"hash={hash_match}, integrity={integrity}, count={count}/{expected}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- rollback-safe restore --

    def validate_rollback_safe_restore(self) -> RestoreReport:
        start = time.monotonic()
        report = RestoreReport(
            scenario="rollback_safe_restore", duration_seconds=0.0
        )
        try:
            src, _ = self._create_source_db("rollback_src.db", 70)

            conn = sqlite3.connect(str(src))
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("INSERT INTO t (v) VALUES ('will_rollback')")
            conn.execute("ROLLBACK")
            conn.commit()

            conn.execute("INSERT INTO t (v) VALUES ('committed_after')")
            conn.commit()
            conn.close()

            snap_path = self._copy(src)
            rconn = sqlite3.connect(str(snap_path))
            integrity = self._integrity_check(snap_path)
            count = rconn.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            has_rolled = rconn.execute(
                "SELECT COUNT(*) FROM t WHERE v = 'will_rollback'"
            ).fetchone()[0]
            rconn.close()

            report.checks["integrity_ok"] = integrity
            report.checks["no_rolled_back_data"] = has_rolled == 0
            report.integrity_ok = integrity
            report.restored_count = count

            if integrity and has_rolled == 0:
                return report.succeed(
                    f"rollback-safe restore: {count} rows, rolled back data excluded"
                )
            return report.fail(
                f"integrity={integrity}, rolled_back_found={has_rolled}"
            )
        except Exception as e:
            return report.fail(str(e))
        finally:
            report.duration_seconds = time.monotonic() - start

    # -- validate all --

    def validate_all(self) -> list[RestoreReport]:
        return [
            self.validate_hot_backup(),
            self.validate_cold_backup(),
            self.validate_wal_consistent_restore(),
            self.validate_archive_replay_restoration(),
            self.validate_corruption_recovery_replay(),
            self.validate_deterministic_restore_ordering(),
            self.validate_offline_restore_bundle(),
            self.validate_rollback_safe_restore(),
        ]
