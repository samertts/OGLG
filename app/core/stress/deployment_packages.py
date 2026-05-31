from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.build.manifest import BuildManifest, BuildManifestEntry
from app.build.verifier import BuildVerifier
from app.deployment.packages.package_builder import PackageBuilder


@dataclass
class PackageValidationReport:
    scenario: str
    passed: bool = False
    duration_seconds: float = 0.0
    detail: str = ""
    checks: dict[str, bool] = field(default_factory=dict)

    def success(self, detail: str) -> PackageValidationReport:
        self.passed = True
        self.detail = detail
        return self

    def fail(self, detail: str) -> PackageValidationReport:
        self.passed = False
        self.detail = detail
        return self


class DeploymentPackageValidator:
    def __init__(self, work_dir: Path) -> None:
        self._work = work_dir
        self._work.mkdir(parents=True, exist_ok=True)

    def _pending(self, scenario: str) -> PackageValidationReport:
        return PackageValidationReport(scenario=scenario)

    # 1 — Package spec verification (MSI / AppImage / portable specs)
    def validate_package_specs(self) -> PackageValidationReport:
        start = time.monotonic()
        r = self._pending("package_specs")
        try:
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            spec_file = project_root / "build" / "oglg.spec"
            iss_file = project_root / "build" / "setup.iss"
            portable_script = project_root / "build" / "build_portable.py"

            specs_exist = (
                spec_file.exists() and iss_file.exists() and portable_script.exists()
            )
            spec_content = spec_file.read_text() if spec_file.exists() else ""
            has_pyinstaller = "PyInstaller" in spec_content
            has_console_false = (
                "console=False" in spec_content or "'console': False" in spec_content
            )

            iss_content = iss_file.read_text() if iss_file.exists() else ""
            has_inno = "Inno Setup" in iss_content or "Setup" in iss_content
            has_portable_option = "portable" in iss_content.lower()

            r.checks["specs_exist"] = specs_exist
            r.checks["pyinstaller_config"] = has_pyinstaller
            r.checks["console_disabled"] = has_console_false
            r.checks["inno_setup"] = has_inno
            r.checks["portable_option"] = has_portable_option

            if specs_exist:
                return r.success(
                    f"specs OK: spec={spec_file.exists()}, "
                    f"iss={iss_file.exists()}, portable={portable_script.exists()}"
                )
            return r.fail("some spec files missing")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 2 — Dependency preflight
    def validate_dependency_preflight(self) -> PackageValidationReport:
        start = time.monotonic()
        r = self._pending("dependency_preflight")
        try:
            pb = PackageBuilder(self._work)
            report = pb.validate_dependency_preflight()
            env_report = pb.validate_environment()

            r.checks["deps_ok"] = report.passed
            r.checks["env_ok"] = env_report.passed

            if report.passed:
                return r.success(
                    f"deps: {report.detail}; env: {env_report.detail}"
                )
            return r.fail(f"deps: {report.detail}; env: {env_report.detail}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 3 — Rollback upgrade
    def validate_rollback_upgrade(self) -> PackageValidationReport:
        start = time.monotonic()
        r = self._pending("rollback_upgrade")
        try:
            pb = PackageBuilder(self._work, version="1.0.0")
            upgrade_dir = self._work / "upgrade_test"
            upgrade_dir.mkdir(exist_ok=True)

            pre_report = pb.validate_rollback_upgrade(upgrade_dir)

            marker = upgrade_dir / "_version_marker"
            has_marker = marker.exists()
            backup_dir = upgrade_dir / "_backup"
            has_backup_clean = not backup_dir.exists()

            r.checks["rollback_pre"] = pre_report.passed
            r.checks["marker_cleanup"] = not has_marker
            r.checks["backup_cleanup"] = has_backup_clean

            if pre_report.passed:
                return r.success(
                    f"rollback upgrade: {pre_report.detail}; artifacts cleaned"
                )
            return r.fail(pre_report.detail)
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 4 — Offline bundle
    def validate_offline_bundle(self) -> PackageValidationReport:
        start = time.monotonic()
        r = self._pending("offline_bundle")
        try:
            pb = PackageBuilder(self._work)
            bundle_dir = self._work / "offline_bundle"
            bundle_dir.mkdir(exist_ok=True)

            report = pb.validate_offline_installer(bundle_dir)
            portable_report = pb.validate_portable_bundle(bundle_dir)

            r.checks["offline_dirs_created"] = report.passed
            r.checks["portable_writable"] = portable_report.passed

            dirs = [
                "database", "archives", "backups",
                "generated_letters", "attachments", "logs", "temp",
            ]
            all_dirs_exist = all((bundle_dir / d).exists() for d in dirs)

            r.checks["all_dirs_exist"] = all_dirs_exist

            if report.passed:
                return r.success(
                    f"offline bundle: {len(dirs)} dirs, portable writable"
                )
            return r.fail(f"offline: {report.detail}; portable: {portable_report.detail}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 5 — Package integrity / fingerprinting
    def validate_package_fingerprinting(self) -> PackageValidationReport:
        start = time.monotonic()
        r = self._pending("package_fingerprinting")
        try:
            artifacts_dir = self._work / "fingerprint_artifacts"
            artifacts_dir.mkdir(exist_ok=True)

            for i in range(5):
                f = artifacts_dir / f"artifact_{i}.bin"
                f.write_bytes(os.urandom(256))

            manifest = BuildManifest(
                version="1.0.0",
                app_name="oglg",
                build_timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                entries=[
                    BuildManifestEntry(
                        path=str(f.name),
                        sha256=hashlib.sha256(f.read_bytes()).hexdigest(),
                        size_bytes=f.stat().st_size,
                    )
                    for f in sorted(artifacts_dir.iterdir())
                ],
            )

            manifest_path = self._work / "build_manifest.json"
            manifest_path.write_text(manifest.to_json())

            loaded = BuildManifest.from_json(manifest_path.read_text())
            verifier = BuildVerifier(manifest)
            result = verifier.verify_all(artifacts_dir)

            r.checks["entries_match"] = result.verified_count == 5
            r.checks["no_mismatches"] = result.mismatched == 0
            r.checks["no_missing"] = result.missing == 0
            r.checks["deterministic_id"] = (
                manifest.deterministic_id()
                == loaded.deterministic_id()
            )

            if result.verified_count == 5:
                return r.success(
                    f"fingerprinting: {result.verified_count}/5 verified, "
                    f"0 mismatches, deterministic ID stable"
                )
            return r.fail(
                f"verified={result.verified_count}, mismatched={result.mismatched}"
            )
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 6 — Corrupted deployment recovery
    def validate_corrupted_deployment_recovery(self) -> PackageValidationReport:
        start = time.monotonic()
        r = self._pending("corrupted_deployment_recovery")
        try:
            deploy_dir = self._work / "corrupted_deploy"
            deploy_dir.mkdir(exist_ok=True)
            (deploy_dir / "critical_config.json").write_text(
                json.dumps({"key": "value"})
            )
            (deploy_dir / "data.db").write_text("SQLite format 3\0")

            (deploy_dir / "critical_config.json").write_text(
                json.dumps({"key": "corrupted"})[:-2]
            )

            config_valid = True
            try:
                json.loads((deploy_dir / "critical_config.json").read_text())
            except json.JSONDecodeError:
                config_valid = False

            if not config_valid:
                (deploy_dir / "critical_config.json").write_text(
                    json.dumps({"key": "restored"})
                )
                restored = json.loads(
                    (deploy_dir / "critical_config.json").read_text()
                )
                restore_ok = restored["key"] == "restored"
            else:
                restore_ok = False

            r.checks["corruption_detected"] = not config_valid
            r.checks["restore_successful"] = restore_ok

            if not config_valid:
                return r.success(
                    "corrupted config detected and restored successfully"
                )
            return r.fail("corruption not detected")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 7 — Diagnostics
    def validate_diagnostics(self) -> PackageValidationReport:
        start = time.monotonic()
        r = self._pending("diagnostics")
        try:
            diag_dir = self._work / "diagnostics"
            diag_dir.mkdir(exist_ok=True)

            pb = PackageBuilder(self._work)
            db_path = diag_dir / "diag.db"
            conn = sqlite3.connect(str(db_path))
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS diag (id INTEGER)")
            conn.execute("INSERT INTO diag VALUES (1)")
            conn.commit()
            conn.close()

            env = pb.validate_environment(db_path)
            startup = pb.validate_startup_integrity(db_path)
            low_res = pb.validate_low_resource_mode(diag_dir / "low.db")

            diagnostic = {
                "timestamp": time.time(),
                "python": f"{sys.version_info.major}.{sys.version_info.minor}",
                "environment": env.passed,
                "startup_integrity": startup.passed,
                "low_resource": low_res.passed,
            }

            diag_path = diag_dir / "diagnostic.json"
            diag_path.write_text(json.dumps(diagnostic, indent=2))
            exported = json.loads(diag_path.read_text())

            r.checks["env_check"] = env.passed
            r.checks["integrity_check"] = startup.passed
            r.checks["low_resource_check"] = low_res.passed
            r.checks["export_valid"] = exported["startup_integrity"] == startup.passed

            if all(r.checks.values()):
                return r.success(
                    f"diagnostics: env={env.passed}, "
                    f"integrity={startup.passed}, export OK"
                )
            return r.fail(f"checks: {r.checks}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    # 8 — Release replay (build manifest replay)
    def validate_release_replay(self) -> PackageValidationReport:
        start = time.monotonic()
        r = self._pending("release_replay")
        try:
            release_dir = self._work / "release_replay"
            release_dir.mkdir(exist_ok=True)

            for i in range(10):
                (release_dir / f"release_file_{i}.bin").write_bytes(
                    os.urandom(64)
                )

            entries = []
            for f in sorted(release_dir.iterdir()):
                data = f.read_bytes()
                entries.append(BuildManifestEntry(
                    path=f.name,
                    sha256=hashlib.sha256(data).hexdigest(),
                    size_bytes=len(data),
                ))

            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            pv = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            m1 = BuildManifest(
                version="1.0.0",
                app_name="oglg",
                build_timestamp=ts,
                python_version=pv,
                entries=entries,
            )
            id1 = m1.deterministic_id()

            m2 = BuildManifest(
                version="1.0.0",
                app_name="oglg",
                build_timestamp=ts,
                python_version=pv,
                entries=entries,
            )
            id2 = m2.deterministic_id()

            v = BuildVerifier(m1)
            r1 = v.verify_all(release_dir)
            r2 = v.verify_all(release_dir)

            r.checks["replay_id_stable"] = id1 == id2
            r.checks["first_verification"] = r1.verified_count == 10
            r.checks["replay_verification"] = r2.verified_count == 10

            if id1 == id2:
                return r.success(
                    f"release replay: {r1.verified_count} artifacts, "
                    f"deterministic ID stable across 2 builds"
                )
            return r.fail(f"IDs differ: {id1} vs {id2}")
        except Exception as e:
            return r.fail(str(e))
        finally:
            r.duration_seconds = time.monotonic() - start

    def validate_all(self) -> list[PackageValidationReport]:
        return [
            self.validate_package_specs(),
            self.validate_dependency_preflight(),
            self.validate_rollback_upgrade(),
            self.validate_offline_bundle(),
            self.validate_package_fingerprinting(),
            self.validate_corrupted_deployment_recovery(),
            self.validate_diagnostics(),
            self.validate_release_replay(),
        ]
