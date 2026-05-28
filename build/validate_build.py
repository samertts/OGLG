#!/usr/bin/env python3
"""Build artifact validation script.

Validates the integrity and completeness of build artifacts
before release. Run after PyInstaller build or ZIP creation.

Usage:
    python build/validate_build.py --build-dir ./build/pyinstaller_dist/OfflineCorrespondenceSystem
    python build/validate_build.py --zip ./dist/OfflineCorrespondenceSystem_Portable_1.0.0.zip
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate build artifacts before release",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--build-dir",
        help="Path to the PyInstaller one-folder build directory",
    )
    group.add_argument(
        "--zip",
        dest="zip_path",
        help="Path to a portable ZIP distribution",
    )
    parser.add_argument("--strict", action="store_true", help="Fail on warnings")
    return parser.parse_args(argv)


def validate_executable_build(build_dir: Path, strict: bool) -> int:
    """Validate a PyInstaller one-folder build directory.

    Args:
        build_dir: Path to the build output directory.
        strict: If True, warnings become errors.

    Returns:
        Exit code (0 = pass, 1 = failure).
    """
    print(f"\n{'=' * 60}")
    print(f"Validating build directory: {build_dir}")
    print(f"{'=' * 60}")

    errors: list[str] = []
    warnings: list[str] = []

    # Check directory exists
    if not build_dir.is_dir():
        errors.append(f"Build directory not found: {build_dir}")
        _report(errors, warnings)
        return 1

    # Required files
    if sys.platform == "win32":
        exe_name = "OfflineCorrespondenceSystem.exe"
    else:
        exe_name = "OfflineCorrespondenceSystem"

    checks: dict[str, bool] = {}

    # Main executable
    exe_path = build_dir / exe_name
    checks["executable_exists"] = exe_path.exists()
    if not exe_path.exists():
        errors.append(f"Main executable missing: {exe_path}")
    elif exe_path.stat().st_size == 0:
        errors.append("Main executable is empty")

    # Python runtime DLLs (Windows)
    if sys.platform == "win32":
        python_dll = list(build_dir.glob("python3*.dll"))
        checks["python_dll"] = len(python_dll) >= 1
        if not python_dll:
            warnings.append("No Python DLL found in build directory")

    # Critical directories in bundle
    bundle_subdirs = [
        "app/config",
        "app/database",
    ]
    for subdir in bundle_subdirs:
        path = build_dir / subdir
        checks[f"dir_{subdir.replace('/', '_')}"] = path.is_dir()
        if not path.is_dir():
            warnings.append(f"Bundle subdirectory missing: {subdir}")

    # Check for assets directory
    assets_dir = build_dir / "assets"
    if assets_dir.is_dir():
        fonts = list(assets_dir.glob("fonts/*"))
        checks["fonts_bundled"] = len(fonts) >= 1
        if not fonts:
            warnings.append("No fonts found in assets/fonts")
    else:
        checks["fonts_bundled"] = False
        warnings.append("Assets directory not found in bundle")

    # Check Alembic migrations
    migrations_dir = build_dir / "app" / "database" / "migrations"
    if migrations_dir.is_dir():
        versions = list(migrations_dir.glob("versions/*.py"))
        checks["migrations_bundled"] = len(versions) >= 1
        if not versions:
            errors.append("No migration scripts found")
    else:
        checks["migrations_bundled"] = False
        errors.append("Migrations directory not found in bundle")

    # Check defaults.json
    defaults = build_dir / "app" / "config" / "defaults.json"
    checks["defaults_json"] = defaults.exists()
    if not defaults.exists():
        errors.append("defaults.json not found in bundle")

    # Compute total size
    total_size = sum(f.stat().st_size for f in build_dir.rglob("*") if f.is_file())
    checks["total_size_mb"] = total_size / (1024 * 1024)
    print(f"  Total bundle size: {checks['total_size_mb']:.1f} MB")

    # Report
    for check, result in checks.items():
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {check}")

    return _report(errors, warnings, strict)


def validate_portable_zip(zip_path: Path, strict: bool) -> int:
    """Validate a portable ZIP distribution.

    Args:
        zip_path: Path to the ZIP file.
        strict: If True, warnings become errors.

    Returns:
        Exit code (0 = pass, 1 = failure).
    """
    print(f"\n{'=' * 60}")
    print(f"Validating portable ZIP: {zip_path}")
    print(f"{'=' * 60}")

    errors: list[str] = []
    warnings: list[str] = []

    if not zip_path.exists():
        errors.append(f"ZIP file not found: {zip_path}")
        _report(errors, warnings)
        return 1

    if zip_path.stat().st_size == 0:
        errors.append("ZIP file is empty")
        _report(errors, warnings)
        return 1

    # Verify ZIP integrity
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                errors.append(f"ZIP corruption detected in: {bad}")

            names = zf.namelist()
            print(f"  Files in archive: {len(names)}")
            print(f"  Archive size: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")

            # Required entries
            required_files = ["portable.txt"]
            required_prefixes = [
                "data/",
                "data/database/",
                "data/archives/",
                "data/backups/",
                "data/logs/",
                "data/temp/",
                "config/",
            ]
            for req in required_files:
                if req not in names:
                    errors.append(f"Required file missing in ZIP: {req}")
            for prefix in required_prefixes:
                if not any(n.startswith(prefix) for n in names):
                    warnings.append(f"Required directory prefix missing in ZIP: {prefix}")

            # Check for executable
            exe_name = "OfflineCorrespondenceSystem.exe"
            if exe_name not in names:
                if "OfflineCorrespondenceSystem" not in names:
                    errors.append(f"Executable not found in ZIP: {exe_name}")

    except zipfile.BadZipFile:
        errors.append("ZIP file is corrupted")
    except Exception as exc:
        errors.append(f"ZIP validation error: {exc}")

    # Verify checksum file exists
    sha_path = zip_path.with_suffix(".sha256.txt")
    if sha_path.exists():
        expected = sha_path.read_text(encoding="utf-8").strip()
        actual_hash = hashlib.sha256(zip_path.read_bytes()).hexdigest()
        if actual_hash not in expected:
            errors.append("SHA-256 checksum mismatch")
        else:
            print(f"  SHA-256: OK ({actual_hash[:16]}...)")
    else:
        warnings.append(f"SHA-256 checksum file missing: {sha_path}")

    return _report(errors, warnings, strict)


def _report(errors: list[str], warnings: list[str], strict: bool = False) -> int:
    if warnings:
        print(f"\n  Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"    ⚠ {w}")
    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for e in errors:
            print(f"    ✗ {e}")
    else:
        print("\n  ✓ No errors")

    if errors:
        return 1
    if strict and warnings:
        return 1
    return 0


def main() -> None:
    args = parse_args()
    if args.build_dir:
        exit_code = validate_executable_build(
            Path(args.build_dir).resolve(),
            strict=args.strict,
        )
    else:
        exit_code = validate_portable_zip(
            Path(args.zip_path).resolve(),
            strict=args.strict,
        )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
