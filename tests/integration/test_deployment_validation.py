from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.deployment.deployment_validator import DeploymentValidator


class TestWindowsDeployment:
    def test_writable_nt_path(self, tmp_path: Path):
        v = DeploymentValidator()
        report = v.validate_windows_deployment(tmp_path)
        assert report.passed

    def test_user_writable_dir(self, tmp_path: Path):
        v = DeploymentValidator()
        report = v.validate_windows_deployment(tmp_path / "AppData" / "Local")
        report.detail = report.detail.replace("OGLG", "appdata")
        assert report.passed


class TestLinuxDeployment:
    def test_var_subdir_isolation(self, tmp_path: Path):
        v = DeploymentValidator()
        report = v.validate_linux_deployment(tmp_path)
        assert report.passed

    def test_user_writable_fallback(self, tmp_path: Path):
        v = DeploymentValidator()
        report = v.validate_linux_deployment(tmp_path / "home" / "user" / ".local")
        assert report.passed


class TestLowMemoryDeployment:
    def test_reduced_limits(self, tmp_path: Path):
        db = tmp_path / "lowmem.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.close()
        v = DeploymentValidator()
        report = v.validate_low_memory_deployment(db)
        assert report.passed


class TestPortableInstallation:
    def test_app_local_dirs(self, tmp_path: Path):
        v = DeploymentValidator()
        report = v.validate_portable_installation(tmp_path)
        assert report.passed


class TestStartupIntegrity:
    def test_integrity_passes(self, tmp_path: Path):
        db = tmp_path / "startup.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.execute("INSERT INTO t VALUES (1)")
        conn.commit()
        conn.close()
        v = DeploymentValidator()
        report = v.validate_startup_integrity(db)
        assert report.passed


class TestRollbackUpgrade:
    def test_rollback_marker_works(self, tmp_path: Path):
        v = DeploymentValidator()
        report = v.validate_rollback_safe_upgrade(tmp_path)
        assert report.passed


class TestCorruptedStartup:
    def test_reinitialization(self, tmp_path: Path):
        db = tmp_path / "corrupt.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.execute("INSERT INTO t VALUES (1)")
        conn.commit()
        conn.close()
        with open(db, "r+b") as f:
            f.seek(100)
            f.write(b"\x00" * 50)
        v = DeploymentValidator()
        report = v.validate_corrupted_startup(db)
        assert report.scenario == "corrupted_startup"


class TestSafeModeStartup:
    def test_restricted_mode(self, tmp_path: Path):
        db = tmp_path / "safemode.db"
        conn = sqlite3.connect(str(db), timeout=5.0)
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.execute("INSERT INTO t VALUES (1)")
        conn.commit()
        conn.close()
        v = DeploymentValidator()
        report = v.validate_safe_mode_startup(db)
        assert report.passed
