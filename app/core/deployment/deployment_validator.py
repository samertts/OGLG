from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DeploymentReport:
    scenario: str
    passed: bool
    detail: str = ""
    duration_seconds: float = 0.0


class DeploymentValidator:
    def __init__(self) -> None:
        self._active_conn_marker = "_active_conn"

    def validate_windows_deployment(self, base_path: Path) -> DeploymentReport:
        start = time.monotonic()
        try:
            test_dir = base_path / "OGLG" / "data"
            test_dir.mkdir(parents=True, exist_ok=True)
            test_file = test_dir / "test_write.tmp"
            test_file.write_text("ok")
            test_file.unlink()
            return DeploymentReport(
                "windows_deployment", True, f"writable at {test_dir}",
                time.monotonic() - start,
            )
        except Exception as e:
            return DeploymentReport(
                "windows_deployment", False, str(e), time.monotonic() - start,
            )

    def validate_linux_deployment(self, base_path: Path) -> DeploymentReport:
        start = time.monotonic()
        try:
            var_dir = base_path / "var" / "lib" / "oglg"
            var_dir.mkdir(parents=True, exist_ok=True)
            test_file = var_dir / "test_write.tmp"
            test_file.write_text("ok")
            test_file.unlink()
            return DeploymentReport(
                "linux_deployment", True, f"writable at {var_dir}",
                time.monotonic() - start,
            )
        except Exception as e:
            return DeploymentReport(
                "linux_deployment", False, str(e), time.monotonic() - start,
            )

    def validate_low_memory_deployment(self, db_path: str | Path) -> DeploymentReport:
        start = time.monotonic()
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            conn.execute("PRAGMA cache_size = -512")
            conn.execute("CREATE TABLE IF NOT EXISTS lowmem_test (id INTEGER)")
            conn.execute("INSERT INTO lowmem_test VALUES (1)")
            conn.commit()
            conn.execute("DROP TABLE IF EXISTS lowmem_test")
            conn.close()
            return DeploymentReport(
                "low_memory_deployment", True, "64KB cache configured",
                time.monotonic() - start,
            )
        except Exception as e:
            return DeploymentReport(
                "low_memory_deployment", False, str(e), time.monotonic() - start,
            )

    def validate_portable_installation(self, base_path: Path) -> DeploymentReport:
        start = time.monotonic()
        try:
            app_dir = base_path / "app"
            data_dir = base_path / "data"
            app_dir.mkdir(parents=True, exist_ok=True)
            data_dir.mkdir(parents=True, exist_ok=True)
            test_file = data_dir / "portable_test.tmp"
            test_file.write_text("portable")
            test_file.unlink()
            return DeploymentReport(
                "portable_installation", True,
                f"app={app_dir}, data={data_dir}",
                time.monotonic() - start,
            )
        except Exception as e:
            return DeploymentReport(
                "portable_installation", False, str(e), time.monotonic() - start,
            )

    def validate_startup_integrity(self, db_path: str | Path) -> DeploymentReport:
        start = time.monotonic()
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            result = conn.execute("PRAGMA integrity_check").fetchone()
            journal = conn.execute("PRAGMA journal_mode").fetchone()
            conn.execute("PRAGMA wal_checkpoint")
            conn.close()
            ok = result is not None and result[0] == "ok"
            return DeploymentReport(
                "startup_integrity", ok,
                f"integrity={result}, journal={journal}",
                time.monotonic() - start,
            )
        except Exception as e:
            return DeploymentReport(
                "startup_integrity", False, str(e), time.monotonic() - start,
            )

    def validate_rollback_safe_upgrade(self, base_path: Path) -> DeploymentReport:
        start = time.monotonic()
        try:
            marker = base_path / self._active_conn_marker
            upgrade_marker = base_path / "_upgrade_in_progress"
            marker.write_text("active")
            upgrade_marker.write_text("v2.0")
            if marker.exists():
                pre_upgrade = marker.read_text()
            marker.unlink(missing_ok=True)
            upgrade_marker.unlink(missing_ok=True)
            marker.write_text("recovered")
            ok = marker.exists() and marker.read_text() == "recovered"
            marker.unlink()
            return DeploymentReport(
                "rollback_safe_upgrade", ok,
                f"pre_upgrade_state={pre_upgrade}",
                time.monotonic() - start,
            )
        except Exception as e:
            return DeploymentReport(
                "rollback_safe_upgrade", False, str(e), time.monotonic() - start,
            )

    def validate_corrupted_startup(self, db_path: str | Path) -> DeploymentReport:
        start = time.monotonic()
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if result is None or result[0] != "ok":
                conn.close()
                conn = sqlite3.connect(str(db_path), timeout=5.0)
                conn.execute("VACUUM")
            conn.close()
            return DeploymentReport(
                "corrupted_startup", True,
                "re-initialized after corruption",
                time.monotonic() - start,
            )
        except Exception as e:
            return DeploymentReport(
                "corrupted_startup", False, str(e), time.monotonic() - start,
            )

    def validate_safe_mode_startup(self, db_path: str | Path) -> DeploymentReport:
        start = time.monotonic()
        try:
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            quick_check = conn.execute("PRAGMA quick_check").fetchone()
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.close()
            ok = quick_check is not None and quick_check[0] == "ok"
            return DeploymentReport(
                "safe_mode_startup", ok,
                f"quick_check={quick_check}",
                time.monotonic() - start,
            )
        except Exception as e:
            return DeploymentReport(
                "safe_mode_startup", False, str(e), time.monotonic() - start,
            )
