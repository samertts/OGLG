from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from app.core.deployment.contracts import DeploymentConfig, DeploymentMode

logger = logging.getLogger(__name__)


class StartupPipeline:
    """Deterministic startup validation pipeline with safe-mode fallback."""

    def __init__(self, config: DeploymentConfig) -> None:
        self._config = config
        self._checks: list[dict[str, Any]] = []
        self._started_at: float = 0.0

    def validate(self) -> bool:
        self._started_at = time.monotonic()
        self._checks = []

        self._run_check("data_dir", self._check_data_dir)
        self._run_check("db_path", self._check_db_path)
        self._run_check("temp_dir", self._check_temp_dir)
        self._run_check("log_dir", self._check_log_dir)
        self._run_check("disk_space", self._check_disk_space)
        self._run_check("python_version", self._check_python_version)

        all_pass = all(c["passed"] for c in self._checks)
        if not all_pass and self._config.safe_mode_on_failure:
            self._config.mode = DeploymentMode.SAFE_MODE
            logger.warning("Startup checks failed — entering SAFE MODE")
        return all_pass

    def _run_check(
        self, name: str, check_fn: Any
    ) -> None:
        try:
            result = check_fn()
            self._checks.append(
                {
                    "check": name,
                    "passed": result.get("passed", False),
                    "message": result.get("message", ""),
                }
            )
        except Exception as exc:
            self._checks.append(
                {
                    "check": name,
                    "passed": False,
                    "message": str(exc),
                }
            )

    def _check_data_dir(self) -> dict[str, Any]:
        path = Path(self._config.data_dir) if self._config.data_dir else Path.cwd() / "data"
        passed = True
        try:
            path.mkdir(parents=True, exist_ok=True)
            test_file = path / ".startup_test"
            test_file.write_text("ok")
            test_file.unlink()
        except (OSError, PermissionError) as exc:
            passed = False
            return {"passed": False, "message": str(exc)}
        return {"passed": passed, "message": f"Data dir ok: {path}"}

    def _check_db_path(self) -> dict[str, Any]:
        path = Path(self._config.db_path) if self._config.db_path else Path.cwd() / "database"
        passed = True
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as exc:
            passed = False
            return {"passed": False, "message": str(exc)}
        return {"passed": passed, "message": f"DB path ok: {path.parent}"}

    def _check_temp_dir(self) -> dict[str, Any]:
        path = Path(self._config.temp_dir) if self._config.temp_dir else Path.cwd() / "temp"
        passed = True
        try:
            path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as exc:
            passed = False
            return {"passed": False, "message": str(exc)}
        return {"passed": passed, "message": f"Temp dir ok: {path}"}

    def _check_log_dir(self) -> dict[str, Any]:
        path = Path(self._config.log_dir) if self._config.log_dir else Path.cwd() / "logs"
        passed = True
        try:
            path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as exc:
            passed = False
            return {"passed": False, "message": str(exc)}
        return {"passed": passed, "message": f"Log dir ok: {path}"}

    def _check_disk_space(self) -> dict[str, Any]:
        try:
            path = self._config.data_dir or "."
            usage = os.statvfs(path)
            free_bytes = usage.f_frsize * usage.f_bavail
            free_mb = free_bytes / (1024 * 1024)
            if free_mb < 50:
                return {"passed": False, "message": f"Low disk space: {free_mb:.0f} MB free"}
            return {"passed": True, "message": f"Disk space ok: {free_mb:.0f} MB free"}
        except Exception as exc:
            return {"passed": True, "message": f"Disk check skipped: {exc}"}

    def _check_python_version(self) -> dict[str, Any]:
        major, minor = sys.version_info[:2]
        if (major, minor) < (3, 10):
            return {"passed": False, "message": f"Python {major}.{minor} < 3.10 required"}
        return {"passed": True, "message": f"Python {major}.{minor} ok"}

    @property
    def results(self) -> list[dict[str, Any]]:
        return list(self._checks)

    @property
    def all_passed(self) -> bool:
        return all(c["passed"] for c in self._checks)

    @property
    def duration(self) -> float:
        return time.monotonic() - self._started_at

    def summary(self) -> dict[str, Any]:
        return {
            "passed": self.all_passed,
            "mode": self._config.mode.value,
            "duration_seconds": self.duration,
            "checks": self.results,
            "config": self._config.to_dict(),
        }
