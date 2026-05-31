from __future__ import annotations

import sqlite3
from pathlib import Path

from app.deployment.packages import PackageBuilder


class TestWindowsMsiEnvironment:
    def test_msi_spec_valid(self, tmp_path: Path):
        b = PackageBuilder(tmp_path)
        report = b.validate_windows_msi_environment()
        assert report.passed


class TestLinuxAppImageEnvironment:
    def test_appimage_spec_valid(self, tmp_path: Path):
        b = PackageBuilder(tmp_path)
        report = b.validate_linux_appimage_environment()
        assert report.passed


class TestPortableBundle:
    def test_portable_dirs_created(self, tmp_path: Path):
        b = PackageBuilder(tmp_path)
        report = b.validate_portable_bundle(tmp_path / "portable")
        assert report.passed


class TestOfflineInstaller:
    def test_offline_dirs_created(self, tmp_path: Path):
        b = PackageBuilder(tmp_path)
        report = b.validate_offline_installer(tmp_path / "offline")
        assert report.passed


class TestRollbackUpgrade:
    def test_version_markers(self, tmp_path: Path):
        b = PackageBuilder(tmp_path, version="1.0.0")
        report = b.validate_rollback_upgrade(tmp_path)
        assert report.passed


class TestEnvironmentValidation:
    def test_python_version(self, tmp_path: Path):
        b = PackageBuilder(tmp_path)
        report = b.validate_environment()
        assert report.passed

    def test_sqlite_version(self, tmp_path: Path):
        db = tmp_path / "env_test.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.close()
        b = PackageBuilder(tmp_path)
        report = b.validate_environment(db)
        assert report.passed


class TestStartupIntegrity:
    def test_db_integrity(self, tmp_path: Path):
        db = tmp_path / "startup.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.execute("INSERT INTO t VALUES (1)")
        conn.commit()
        conn.close()
        b = PackageBuilder(tmp_path)
        report = b.validate_startup_integrity(db)
        assert report.passed


class TestDependencyPreflight:
    def test_all_deps_available(self, tmp_path: Path):
        b = PackageBuilder(tmp_path)
        report = b.validate_dependency_preflight()
        assert report.passed


class TestLowResourceMode:
    def test_low_resource_db(self, tmp_path: Path):
        db = tmp_path / "low.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.close()
        b = PackageBuilder(tmp_path)
        report = b.validate_low_resource_mode(db)
        assert report.passed


class TestSafeModeLauncher:
    def test_safe_config_created(self, tmp_path: Path):
        b = PackageBuilder(tmp_path)
        report = b.validate_safe_mode_launcher(tmp_path / "safe")
        assert report.passed


class TestBuildSpec:
    def test_spec_has_metadata(self, tmp_path: Path):
        b = PackageBuilder(tmp_path, version="2.0.0")
        spec = b.build_spec()
        assert spec.version == "2.0.0"
        assert "python" in spec.environment
        assert "platform" in spec.environment


class TestRunAll:
    def test_all_preflight_execute(self, tmp_path: Path):
        db = tmp_path / "all_preflight.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.execute("INSERT INTO t VALUES (1)")
        conn.commit()
        conn.close()
        b = PackageBuilder(tmp_path)
        reports = b.run_all_preflight(tmp_path / "deploy", db)
        assert len(reports) == 10
        passed = sum(1 for r in reports if r.passed)
        assert passed >= 9
