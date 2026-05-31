from __future__ import annotations

import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path

from app.build.manifest import BuildManifest


@dataclass
class ValidationResult:
    passed: bool
    checks: dict[str, bool] = field(default_factory=dict)
    detail: str = ""


class BuildValidator:
    MIN_PYTHON = (3, 12)
    MIN_SQLITE = (3, 45, 0)

    def validate_environment(self) -> ValidationResult:
        checks: dict[str, bool] = {}

        py_ver = sys.version_info[:2]
        checks["python_version"] = py_ver >= self.MIN_PYTHON[:2]

        sqlite_ver = sqlite3.sqlite_version_info
        checks["sqlite_version"] = sqlite_ver >= self.MIN_SQLITE

        checks["platform_detected"] = sys.platform in ("linux", "win32", "darwin")

        passed = all(checks.values())
        failed = [k for k, v in checks.items() if not v]
        detail = "ok" if passed else f"failed: {', '.join(failed)}"

        return ValidationResult(passed=passed, checks=checks, detail=detail)

    def validate_manifest_determinism(
        self,
        source_paths: list[Path],
        reference_manifest: BuildManifest,
    ) -> ValidationResult:
        checks: dict[str, bool] = {}

        manifest_paths = {e.path for e in reference_manifest.entries}
        source_names = {p.name for p in source_paths}
        checks["entry_count"] = len(reference_manifest.entries) == len(source_paths)
        checks["all_sources_mapped"] = source_names == manifest_paths

        passed = all(checks.values())
        failed = [k for k, v in checks.items() if not v]
        detail = "ok" if passed else f"failed: {', '.join(failed)}"

        return ValidationResult(passed=passed, checks=checks, detail=detail)

    def validate_rollback_safe(self, manifest_path: Path) -> ValidationResult:
        checks: dict[str, bool] = {}
        if manifest_path.exists():
            try:
                m = BuildManifest.from_file(manifest_path)
                checks["manifest_parsed"] = True
                checks["has_entries"] = len(m.entries) > 0
                checks["has_deterministic_id"] = len(m.deterministic_id()) == 64
            except Exception:
                checks["manifest_parsed"] = False
                checks["has_entries"] = False
                checks["has_deterministic_id"] = False
        else:
            checks["manifest_parsed"] = False
            checks["has_entries"] = False
            checks["has_deterministic_id"] = False

        passed = all(checks.values())
        failed = [k for k, v in checks.items() if not v]
        detail = "ok" if passed else f"failed: {', '.join(failed)}"
        return ValidationResult(passed=passed, checks=checks, detail=detail)
