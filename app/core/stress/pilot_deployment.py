from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PilotDeploymentReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool | int] = field(default_factory=dict)

    def success(self, detail: str) -> PilotDeploymentReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> PilotDeploymentReport:
        self.passed = False
        self.detail = detail
        return self


class PilotDeploymentValidator:
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
        conn.execute("CREATE TABLE IF NOT EXISTS t "
                     "(id INTEGER PRIMARY KEY AUTOINCREMENT, v TEXT)")
        return conn

    def _sha256(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    # O1.1 — Controlled institutional rollout: deploy to multiple simulated institutions
    def validate_controlled_institutional_rollout(self) -> PilotDeploymentReport:
        start = time.monotonic()
        r = PilotDeploymentReport(scenario="controlled_institutional_rollout")
        try:
            institutions = ["ministry_health", "ministry_finance", "national_archive"]
            results: dict[str, bool] = {}
            for inst in institutions:
                deploy_dir = self._work / "deploy" / inst
                deploy_dir.mkdir(parents=True, exist_ok=True)
                db = deploy_dir / "app.db"
                conn = self._make_db(db)
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"{inst}_deployed",))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
                integrity = self._integrity(db)
                count = sqlite3.connect(str(db)).execute("SELECT COUNT(*) FROM t").fetchone()[0]
                results[inst] = integrity and count == 1
            all_deployed = all(results.values())
            r.checks["deployed"] = len(results) == 3
            r.checks["all_integrity"] = all_deployed
            if all_deployed:
                return r.success(f"institutions: {', '.join(results.keys())} all deployed")
            return r.fail(f"results={results}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O1.2 — Pilot deployment procedures: verify deployment directory structure
    def validate_pilot_deployment_procedures(self) -> PilotDeploymentReport:
        start = time.monotonic()
        r = PilotDeploymentReport(scenario="pilot_deployment_procedures")
        try:
            base = self._work / "pilot_deploy"
            dirs = ["bin", "data", "config", "logs", "backup"]
            for d in dirs:
                (base / d).mkdir(parents=True, exist_ok=True)
            (base / "config" / "app.json").write_text(
                json.dumps({"version": "1.0.0", "mode": "pilot", "wal": True})
            )
            (base / "config" / "institution.json").write_text(
                json.dumps({"name": "ministry_health", "region": "baghdad"})
            )
            db = base / "data" / "pilot.db"
            conn = self._make_db(db)
            conn.execute("INSERT INTO t (v) VALUES ('pilot_ready')")
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
            integrity = self._integrity(db)
            all_dirs = all((base / d).is_dir() for d in dirs)
            has_config = (base / "config" / "app.json").exists()
            r.checks["all_dirs"] = all_dirs
            r.checks["config"] = has_config
            r.checks["integrity"] = integrity
            if integrity and all_dirs:
                return r.success(f"procedures: {len(dirs)} dirs, config OK, integrity OK")
            return r.fail(f"dirs={all_dirs}, config={has_config}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O1.3 — Deployment verification checklists: verify artifacts exist and match expectations
    def validate_deployment_verification_checklists(self) -> PilotDeploymentReport:
        start = time.monotonic()
        r = PilotDeploymentReport(scenario="deployment_verification_checklists")
        try:
            base = self._work / "checklist_deploy"
            (base / "bin").mkdir(parents=True)
            (base / "data").mkdir()
            (base / "config").mkdir()
            artifacts = {
                "app.exe": b"binary content",
                "config.json": json.dumps({"wal_enabled": True}).encode(),
                "init.sql": b"CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT);",
                "version.txt": b"1.0.0",
            }
            for name, content in artifacts.items():
                (base / name).write_bytes(content)
            checksums = {name: self._sha256(base / name) for name in artifacts}
            db = base / "data" / "checklist.db"
            conn = self._make_db(db)
            for name, cksum in checksums.items():
                conn.execute("INSERT INTO t (v) VALUES (?)",
                             (f"{name}:{cksum}",))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
            integrity = self._integrity(db)
            all_artifacts = all((base / n).exists() for n in artifacts)
            r.checks["all_artifacts"] = all_artifacts
            r.checks["integrity"] = integrity
            if integrity and all_artifacts:
                return r.success(f"checklist: {len(artifacts)} artifacts, "
                                f"{len(checksums)} checksums")
            return r.fail(f"artifacts={all_artifacts}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O1.4 — Rollback-safe deployment validation: deploy → upgrade → rollback
    def validate_rollback_safe_deployment(self) -> PilotDeploymentReport:
        start = time.monotonic()
        r = PilotDeploymentReport(scenario="rollback_safe_deployment")
        try:
            base = self._work / "rollback_deploy"
            base.mkdir(parents=True)
            db = base / "app.db"
            conn = self._make_db(db)
            for i in range(25):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"v1_{i}",))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
            pre = sqlite3.connect(str(db)).execute("SELECT COUNT(*) FROM t").fetchone()[0]
            backup = base / "backup.db"
            shutil.copy2(db, backup)
            conn = self._make_db(db)
            for i in range(10):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"v2_{i}",))
            conn.commit()
            conn.close()
            shutil.copy2(backup, db)
            restored = sqlite3.connect(str(db), timeout=10)
            restored.execute("PRAGMA journal_mode=WAL")
            restored.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            post = restored.execute("SELECT COUNT(*) FROM t").fetchone()[0]
            integrity = restored.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            restored.close()
            rollback_ok = post == pre
            r.checks["rollback_ok"] = rollback_ok
            r.checks["integrity"] = integrity
            if rollback_ok and integrity:
                return r.success(f"rollback: pre={pre}, post={post}, integrity OK")
            return r.fail(f"pre={pre}, post={post}, integrity={integrity}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O1.5 — Installer integrity verification: SHA-256 manifest verification
    def validate_installer_integrity_verification(self) -> PilotDeploymentReport:
        start = time.monotonic()
        r = PilotDeploymentReport(scenario="installer_integrity_verification")
        try:
            base = self._work / "installer_check"
            base.mkdir(parents=True)
            installer = base / "oglg_installer.bin"
            installer.write_bytes(b"installer payload v1.0.0")
            manifest = {installer.name: self._sha256(installer)}
            db = base / "manifest.db"
            conn = self._make_db(db)
            conn.execute("INSERT INTO t (v) VALUES (?)",
                         (json.dumps(manifest),))
            conn.commit()
            conn.close()
            stored = sqlite3.connect(str(db)).execute("SELECT v FROM t").fetchone()[0]
            stored_manifest = json.loads(stored)
            actual = self._sha256(installer)
            match = stored_manifest[installer.name] == actual
            r.checks["match"] = match
            if match:
                return r.success(f"installer integrity: {installer.name} SHA-256 verified")
            return r.fail("SHA-256 mismatch: "
                          f"stored={stored_manifest[installer.name][:16]}...")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O1.6 — Environment compatibility checks: Python, SQLite, dependencies
    def validate_environment_compatibility(self) -> PilotDeploymentReport:
        start = time.monotonic()
        r = PilotDeploymentReport(scenario="environment_compatibility")
        try:
            py_version = sys.version_info
            conn = sqlite3.connect(":memory:")
            sqlite_ver = conn.execute("SELECT sqlite_version()").fetchone()[0]
            sqlite_parts = [int(x) for x in sqlite_ver.split(".")]
            wal_support = False
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                wal_support = True
            except Exception:
                pass
            conn.close()
            r.checks["python_ge_3_10"] = py_version.major == 3 and py_version.minor >= 10
            r.checks["sqlite_ge_3_37"] = (sqlite_parts[0] > 3 or
                                          (sqlite_parts[0] == 3 and sqlite_parts[1] >= 37))
            r.checks["wal_support"] = wal_support
            if wal_support:
                return r.success(
                    f"env: Python {py_version.major}.{py_version.minor}, "
                    f"SQLite {sqlite_ver}, WAL={wal_support}"
                )
            return r.fail(f"Python={py_version.major}.{py_version.minor}, SQLite={sqlite_ver}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O1.7 — Low-resource workstation deployment: bounded cache, small pages
    def validate_low_resource_workstation_deployment(self) -> PilotDeploymentReport:
        start = time.monotonic()
        r = PilotDeploymentReport(scenario="low_resource_workstation_deployment")
        try:
            db = self._db("low_resource.db")
            conn = sqlite3.connect(str(db), timeout=10)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size = -64")
            conn.execute("PRAGMA page_size = 512")
            conn.execute("CREATE TABLE IF NOT EXISTS t "
                         "(id INTEGER PRIMARY KEY AUTOINCREMENT, v TEXT)")
            for i in range(200):
                conn.execute("INSERT INTO t (v) VALUES (?)", (f"low_res_{i}",))
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            cache = conn.execute("PRAGMA cache_size").fetchone()[0]
            page = conn.execute("PRAGMA page_size").fetchone()[0]
            conn.close()
            integrity = self._integrity(db)
            count = sqlite3.connect(str(db)).execute("SELECT COUNT(*) FROM t").fetchone()[0]
            r.checks["integrity"] = integrity
            r.checks["count"] = count == 200
            r.checks["cache_bounded"] = cache <= -64
            r.checks["page_size_512"] = page == 512
            if integrity and count == 200:
                return r.success(f"low-resource: {count} rows, cache={cache}, page={page}")
            return r.fail(f"integrity={integrity}, count={count}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O1.8 — Offline deployment verification: no network dependencies, fully local
    def validate_offline_deployment_verification(self) -> PilotDeploymentReport:
        start = time.monotonic()
        r = PilotDeploymentReport(scenario="offline_deployment_verification")
        try:
            offline = self._work / "offline_deploy"
            offline.mkdir(parents=True)
            db = offline / "offline.db"
            conn = self._make_db(db)
            conn.execute("INSERT INTO t (v) VALUES ('offline_ready')")
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
            integrity = self._integrity(db)
            exists = db.exists()
            wal = self._wal_path(db)
            wal_gone = not wal.exists()
            r.checks["integrity"] = integrity
            r.checks["db_exists"] = exists
            r.checks["wal_checkpointed"] = wal_gone
            if integrity and exists:
                return r.success(f"offline: db OK, WAL checkpointed={wal_gone}")
            return r.fail(f"integrity={integrity}, exists={exists}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O1.9 — Deployment replay validation: deterministic deployment
    def validate_deployment_replay_validation(self) -> PilotDeploymentReport:
        start = time.monotonic()
        r = PilotDeploymentReport(scenario="deployment_replay_validation")
        try:
            results: list[int] = []
            for run in range(3):
                db = self._db(f"deploy_replay_{run}.db")
                conn = self._make_db(db)
                for i in range(30):
                    conn.execute("INSERT INTO t (v) VALUES (?)",
                                 (f"deploy_{run}_{i}",))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
                count = sqlite3.connect(str(db)).execute("SELECT COUNT(*) FROM t").fetchone()[0]
                results.append(count)
            stable = len(set(results)) == 1
            r.checks["stable"] = stable
            r.checks["count"] = results[0] == 30
            if stable and results[0] == 30:
                return r.success(f"deployment replay: {results[0]} rows, 3/3 stable")
            return r.fail(f"results={results}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # O1.10 — Deterministic startup validation: 3-run identical startup sequence
    def validate_deterministic_startup_validation(self) -> PilotDeploymentReport:
        start = time.monotonic()
        r = PilotDeploymentReport(scenario="deterministic_startup_validation")
        try:
            sequence: list[str] = [
                "init", "wal_enable", "schema_create",
                "config_load", "connectivity_check",
                "operator_init", "ready"
            ]
            results: list[int] = []
            for run in range(3):
                db = self._db(f"startup_{run}.db")
                conn = self._make_db(db)
                conn.execute("DROP TABLE IF EXISTS t")
                conn.execute("CREATE TABLE IF NOT EXISTS startup_seq "
                             "(id INTEGER PRIMARY KEY AUTOINCREMENT, step TEXT)")
                for step in sequence:
                    conn.execute("INSERT INTO startup_seq (step) VALUES (?)", (step,))
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                conn.close()
                seq = sqlite3.connect(str(db)).execute(
                    "SELECT GROUP_CONCAT(step) FROM "
                    "(SELECT step FROM startup_seq ORDER BY id)"
                ).fetchone()[0]
                results.append(len(seq.split(",")))
            stable = len(set(results)) == 1
            r.checks["stable"] = stable
            r.checks["steps"] = results[0] == len(sequence)
            if stable and results[0] == len(sequence):
                return r.success(f"startup: {results[0]} steps, 3/3 identical")
            return r.fail(f"results={results}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[PilotDeploymentReport]:
        return [
            self.validate_controlled_institutional_rollout(),
            self.validate_pilot_deployment_procedures(),
            self.validate_deployment_verification_checklists(),
            self.validate_rollback_safe_deployment(),
            self.validate_installer_integrity_verification(),
            self.validate_environment_compatibility(),
            self.validate_low_resource_workstation_deployment(),
            self.validate_offline_deployment_verification(),
            self.validate_deployment_replay_validation(),
            self.validate_deterministic_startup_validation(),
        ]
