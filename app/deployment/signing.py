"""Code signing preparation utilities.

Provides helpers for future code signing integration without
requiring deployment redesign. Architecture remains compatible
with institutional certificates and hash validation workflows.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def compute_file_hash_sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file for integrity verification.

    Args:
        path: Path to the file.

    Returns:
        Hex-encoded SHA-256 digest string.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_file_hash_sha1(path: Path) -> str:
    """Compute SHA-1 hash of a file for legacy integrity verification.

    Args:
        path: Path to the file.

    Returns:
        Hex-encoded SHA-1 digest string.
    """
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def generate_checksums(directory: Path, patterns: list[str] | None = None) -> dict[str, dict[str, str]]:
    """Generate SHA-256 and SHA-1 checksums for all files in a directory.

    Args:
        directory: Directory to scan.
        patterns: Optional glob patterns to filter files.

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    if patterns is None:
        patterns = ["**/*"]

    checksums: dict[str, dict[str, str]] = {}
    for pattern in patterns:
        for file_path in directory.glob(pattern):
            if file_path.is_file():
                rel = str(file_path.relative_to(directory))
                checksums[rel] = {
                    "sha256": compute_file_hash_sha256(file_path),
                    "sha1": compute_file_hash_sha1(file_path),
                }
    return checksums


def generate_checksum_manifest(directory: Path, output_path: Path) -> None:
    """Generate a JSON checksum manifest for a build directory.

    Args:
        directory: Build output directory.
        output_path: Path to write the manifest JSON file.
    """
    import json

    checksums = generate_checksums(directory)
    manifest = {
        "manifest_version": "1.0",
        "directory": str(directory.resolve()),
        "files": checksums,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def verify_checksum_manifest(directory: Path, manifest_path: Path) -> list[str]:
    """Verify files in a directory against a checksum manifest.

    Args:
        directory: Directory containing the files.
        manifest_path: Path to the checksum manifest JSON.

    Returns:
        List of verification errors (empty if all pass).
    """
    import json

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []

    for rel, expected in manifest.get("files", {}).items():
        file_path = directory / rel
        if not file_path.exists():
            errors.append(f"Missing file: {rel}")
            continue

        actual = compute_file_hash_sha256(file_path)
        if actual != expected.get("sha256", ""):
            errors.append(f"SHA-256 mismatch: {rel}")

    return errors
