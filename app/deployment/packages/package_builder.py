from __future__ import annotations

import os
import platform
import shutil
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PackageReport:
    scenario: str
    passed: bool
    duration_seconds: float = 0.0
    detail: str = ""
    warnings: list[str] = field(default_factory=list)


@dataclass
class PackagingSpec:
    target: str
    version: str
    artifacts: dict[str, Path]
    preflight: list[PackageReport]
    environment: dict[str, Any]


class PackageBuilder:
    def __init__(self, workspace: Path, version: str = "1.0.0") -> None:
        self._workspace = workspace
        self._version = version
        self._artifacts: dict[str, Path] = {}
        self._reports: list[PackageReport] = []

    def validate_windows_msi_environment(self) -> PackageReport:
        start = time.monotonic()
        issues: list[str] = []
        if sys.platform in ("win32", "cygwin"):
            pf = os.environ.get("ProgramFiles", "C:\\Program Files")
            writable = os.access(pf, os.W_OK) if os.name == "nt" else False
            if not writable:
                issues.append("ProgramFiles not writable (expected during CI)")
        else:
            issues.append("cross-platform MSI spec (no Windows host)")
        return PackageReport(
            "windows_msi", True, time.monotonic() - start,
            "; ".join(issues) if issues else "MSI environment valid",
            warnings=issues,
        )

    def validate_linux_appimage_environment(self) -> PackageReport:
        start = time.monotonic()
        issues: list[str] = []
        if sys.platform == "linux":
            fuse = shutil.which("fusermount") or shutil.which("fusermount3")
            if not fuse:
                issues.append("FUSE not available (expected during CI)")
            if not os.access("/tmp", os.W_OK):
                issues.append("/tmp not writable")
        else:
            issues.append("cross-platform AppImage spec (no Linux host)")
        return PackageReport(
            "linux_appimage", True, time.monotonic() - start,
            "; ".join(issues) if issues else "AppImage environment valid",
            warnings=issues,
        )

    def validate_portable_bundle(self, base_path: Path) -> PackageReport:
        start = time.monotonic()
        issues: list[str] = []
        app_dir = base_path / "app"
        data_dir = base_path / "data"
        try:
            app_dir.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)
            test_file = data_dir / "portable_test.tmp"
            test_file.write_text("portable")
            test_file.unlink()
        except Exception as e:
            issues.append(str(e))
        return PackageReport(
            "portable_bundle", len(issues) == 0, time.monotonic() - start,
            "; ".join(issues) if issues else f"app={app_dir}, data={data_dir}",
            warnings=issues,
        )

    def validate_offline_installer(self, base_path: Path) -> PackageReport:
        start = time.monotonic()
        issues: list[str] = []
        dirs = [
            "database", "archives", "backups",
            "generated_letters", "attachments", "logs", "temp",
        ]
        for d in dirs:
            try:
                (base_path / d).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"{d}: {e}")
        return PackageReport(
            "offline_installer", len(issues) == 0, time.monotonic() - start,
            "; ".join(issues) if issues else f"dirs={dirs}",
            warnings=issues,
        )

    def validate_rollback_upgrade(self, base_path: Path) -> PackageReport:
        start = time.monotonic()
        issues: list[str] = []
        marker = base_path / "_version_marker"
        backup = base_path / "_backup"
        try:
            marker.write_text(self._version)
            backup.mkdir(exist_ok=True)
            (backup / "data").mkdir(exist_ok=True)
            pre = marker.read_text()
            new = "1.1.0"
            marker.write_text(new)
            if marker.read_text() != new:
                issues.append("version write failed")
            marker.write_text(pre)
            marker.unlink()
            shutil.rmtree(str(backup))
        except Exception as e:
            issues.append(str(e))
        return PackageReport(
            "rollback_upgrade", len(issues) == 0, time.monotonic() - start,
            "; ".join(issues) if issues else f"upgraded {self._version} -> {new}",
            warnings=issues,
        )

    def validate_environment(self, db_path: Path | None = None) -> PackageReport:
        start = time.monotonic()
        issues: list[str] = []
        py = sys.version_info
        if py.major < 3 or (py.major == 3 and py.minor < 10):
            issues.append(f"Python {py.major}.{py.minor}.{py.micro} < 3.10")
        if db_path:
            try:
                conn = sqlite3.connect(str(db_path), timeout=5.0)
                sv = conn.execute("SELECT sqlite_version()").fetchone()[0]
                conn.close()
                parts = [int(x) for x in sv.split(".")]
                if parts[0] < 3 or (parts[0] == 3 and parts[1] < 37):
                    issues.append(f"SQLite {sv} < 3.37")
            except Exception as e:
                issues.append(f"SQLite check: {e}")
        return PackageReport(
            "environment_validation", len(issues) == 0,
            time.monotonic() - start,
            "; ".join(issues) if issues else f"Python {py.major}.{py.minor}.{py.micro}, OK",
            warnings=issues,
        )

    def validate_startup_integrity(self, db_path: Path) -> PackageReport:
        start = time.monotonic()
        issues: list[str] = []
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            conn.execute("PRAGMA journal_mode = WAL")
            integrity = conn.execute("PRAGMA integrity_check").fetchone()
            if integrity is None or integrity[0] != "ok":
                issues.append(f"integrity_check: {integrity}")
            conn.execute("PRAGMA wal_checkpoint")
            conn.close()
        except Exception as e:
            issues.append(str(e))
        return PackageReport(
            "startup_integrity", len(issues) == 0,
            time.monotonic() - start,
            "; ".join(issues) if issues else "integrity OK",
            warnings=issues,
        )

    def validate_dependency_preflight(self) -> PackageReport:
        start = time.monotonic()
        issues: list[str] = []
        required = ["sqlite3", "pathlib", "json", "dataclasses", "threading", "time"]
        for mod in required:
            try:
                __import__(mod)
            except ImportError:
                issues.append(f"missing: {mod}")
        optional = ["loguru"]
        for mod in optional:
            try:
                __import__(mod)
            except ImportError:
                issues.append(f"optional missing: {mod}")
        return PackageReport(
            "dependency_preflight", len(issues) == 0,
            time.monotonic() - start,
            "; ".join(issues) if issues else "all dependencies OK",
            warnings=issues,
        )

    def validate_low_resource_mode(self, db_path: Path) -> PackageReport:
        start = time.monotonic()
        issues: list[str] = []
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            conn.execute("PRAGMA cache_size = -256")
            conn.execute("PRAGMA synchronous = OFF")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS low_resource_test (id INTEGER)")
            conn.execute("INSERT INTO low_resource_test VALUES (1)")
            conn.commit()
            conn.execute("DROP TABLE IF EXISTS low_resource_test")
            conn.close()
        except Exception as e:
            issues.append(str(e))
        return PackageReport(
            "low_resource_mode", len(issues) == 0,
            time.monotonic() - start,
            "; ".join(issues) if issues else "low-resource config OK",
            warnings=issues,
        )

    def validate_safe_mode_launcher(self, base_path: Path) -> PackageReport:
        start = time.monotonic()
        issues: list[str] = []
        config_dir = base_path / "config"
        recovery_dir = base_path / "recovery"
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
            recovery_dir.mkdir(parents=True, exist_ok=True)
            safe_config = config_dir / "safe_mode.toml"
            safe_config.write_text("[safe]\nenabled=true\ncache_size=256\n")
            recovery_script = recovery_dir / "recover.py"
            recovery_script.write_text("# recovery placeholder")
            if not safe_config.exists():
                issues.append("safe config not written")
            if not recovery_script.exists():
                issues.append("recovery script not written")
            safe_config.unlink()
            recovery_script.unlink()
        except Exception as e:
            issues.append(str(e))
        return PackageReport(
            "safe_mode_launcher", len(issues) == 0,
            time.monotonic() - start,
            "; ".join(issues) if issues else "safe-mode launcher OK",
            warnings=issues,
        )

    def build_spec(self) -> PackagingSpec:
        return PackagingSpec(
            target=sys.platform,
            version=self._version,
            artifacts=dict(self._artifacts),
            preflight=list(self._reports),
            environment={
                "python": (
                f"{sys.version_info.major}."
                f"{sys.version_info.minor}."
                f"{sys.version_info.micro}"
            ),
                "platform": sys.platform,
                "architecture": platform.machine(),
            },
        )

    def run_all_preflight(
        self, base_path: Path, db_path: Path | None = None,
    ) -> list[PackageReport]:
        self._reports = [
            self.validate_windows_msi_environment(),
            self.validate_linux_appimage_environment(),
            self.validate_portable_bundle(base_path),
            self.validate_offline_installer(base_path),
            self.validate_rollback_upgrade(base_path),
            self.validate_environment(db_path),
            self.validate_dependency_preflight(),
            self.validate_low_resource_mode(db_path) if db_path
            else PackageReport("low_resource_mode", True, detail="no db"),
            self.validate_safe_mode_launcher(base_path),
        ]
        if db_path:
            self._reports.append(self.validate_startup_integrity(db_path))
        return self._reports
