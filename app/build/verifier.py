from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from app.build.manifest import BuildManifest


@dataclass
class VerificationResult:
    passed: bool
    verified_count: int
    mismatched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)
    detail: str = ""


class BuildVerifier:
    def __init__(self, manifest: BuildManifest) -> None:
        self._manifest = manifest

    def verify_artifact(self, file_path: Path, expected_hash: str) -> bool:
        if not file_path.exists():
            return False
        actual = hashlib.sha256(file_path.read_bytes()).hexdigest()
        return actual == expected_hash

    def verify_all(self, base_dir: Path) -> VerificationResult:
        mismatched: list[str] = []
        missing: list[str] = []
        extra: list[str] = []
        verified = 0

        manifest_paths = {e.path: e for e in self._manifest.entries}
        for entry in self._manifest.entries:
            full_path = base_dir / entry.path
            if not full_path.exists():
                missing.append(entry.path)
                continue
            actual = hashlib.sha256(full_path.read_bytes()).hexdigest()
            if actual != entry.sha256:
                mismatched.append(entry.path)
            else:
                verified += 1

        if base_dir.is_dir():
            for disk_path in base_dir.rglob("*"):
                if disk_path.is_file():
                    rel = str(disk_path.relative_to(base_dir))
                    if rel not in manifest_paths:
                        extra.append(rel)

        passed = len(missing) == 0 and len(mismatched) == 0
        detail_parts: list[str] = []
        if missing:
            detail_parts.append(f"missing={len(missing)}")
        if mismatched:
            detail_parts.append(f"mismatched={len(mismatched)}")
        if extra:
            detail_parts.append(f"extra={len(extra)}")
        detail = ", ".join(detail_parts) if detail_parts else "all verified"

        return VerificationResult(
            passed=passed,
            verified_count=verified,
            mismatched=mismatched,
            missing=missing,
            extra=extra,
            detail=detail,
        )

    def verify_release_integrity(self, artifact_paths: list[Path]) -> VerificationResult:
        mismatched: list[str] = []
        missing: list[str] = []
        verified = 0

        manifest_entries = {e.path: e for e in self._manifest.entries}
        for ap in artifact_paths:
            name = ap.name
            if name not in manifest_entries:
                missing.append(name)
                continue
            expected = manifest_entries[name]
            actual = hashlib.sha256(ap.read_bytes()).hexdigest()
            if actual != expected.sha256:
                mismatched.append(name)
            else:
                verified += 1

        passed = len(missing) == 0 and len(mismatched) == 0
        detail_parts = []
        if missing:
            detail_parts.append(f"missing={len(missing)}")
        if mismatched:
            detail_parts.append(f"mismatched={len(mismatched)}")
        detail = ", ".join(detail_parts) if detail_parts else "all verified"

        return VerificationResult(
            passed=passed,
            verified_count=verified,
            mismatched=mismatched,
            missing=missing,
            detail=detail,
        )
