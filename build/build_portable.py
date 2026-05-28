#!/usr/bin/env python3
"""Portable deployment build script.

Builds the PyInstaller executable and packages it as a portable ZIP
distribution suitable for USB deployment and air-gapped environments.

Usage:
    python build/build_portable.py [--version 1.0.0] [--output-dir ./dist]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from datetime import datetime


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build portable ZIP distribution of the Correspondence System",
    )
    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Version string for the build (default: 1.0.0)",
    )
    parser.add_argument(
        "--output-dir",
        default="./dist",
        help="Output directory for build artifacts (default: ./dist)",
    )
    parser.add_argument(
        "--skip-pyinstaller",
        action="store_true",
        help="Skip PyInstaller build (re-package existing build)",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not clean the build directory before building",
    )
    return parser.parse_args(argv)


def build_pyinstaller(project_root: Path) -> Path:
    """Run PyInstaller and return the output directory path."""
    spec_path = project_root / "build" / "oglg.spec"
    build_dir = project_root / "build" / "pyinstaller_build"
    dist_dir = project_root / "build" / "pyinstaller_dist"

    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    print(f"[build] Running PyInstaller: {spec_path}")
    result = subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            str(spec_path),
            "--workpath", str(build_dir),
            "--distpath", str(dist_dir),
            "--clean",
        ],
        cwd=str(project_root),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"[ERROR] PyInstaller failed:\n{result.stderr}")
        sys.exit(1)

    print(f"[build] PyInstaller output: {dist_dir}")
    return dist_dir / "OfflineCorrespondenceSystem"


def create_portable_distribution(
    executable_dir: Path,
    output_dir: Path,
    version: str,
) -> tuple[Path, Path]:
    """Package the executable directory into a portable layout.

    Args:
        executable_dir: PyInstaller one-folder output.
        output_dir: Destination for the ZIP file.
        version: Version string.

    Returns:
        Tuple of (zip_path, txt_path) for the ZIP and checksum file.
    """
    portable_name = f"OfflineCorrespondenceSystem_Portable_{version}"
    portable_dir = output_dir / portable_name

    if portable_dir.exists():
        shutil.rmtree(portable_dir)

    print(f"[build] Creating portable distribution: {portable_dir}")

    # Create portable directory layout
    portable_dir.mkdir(parents=True, exist_ok=True)

    # Copy executable and runtime files
    for item in executable_dir.iterdir():
        dest = portable_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, symlinks=False)
        else:
            shutil.copy2(item, dest)

    # Create data directory structure
    data_dirs = [
        "data/database",
        "data/archives",
        "data/backups",
        "data/logs",
        "data/temp",
        "data/attachments",
        "data/generated_letters",
        "config",
    ]
    for dir_path in data_dirs:
        (portable_dir / dir_path).mkdir(parents=True, exist_ok=True)

    # Create portable.txt marker
    (portable_dir / "portable.txt").write_text(
        f"OGLG Portable Mode\nVersion: {version}\nCreated: {datetime.now().isoformat()}\n",
        encoding="utf-8",
    )

    print(f"[build] Creating ZIP archive...")
    zip_path = output_dir / f"{portable_name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in portable_dir.rglob("*"):
            if file_path.is_file():
                arcname = str(file_path.relative_to(portable_dir))
                zf.write(file_path, arcname)

    print(f"[build] ZIP archive created: {zip_path} ({zip_path.stat().st_size / 1024 / 1024:.1f} MB)")

    # Clean up uncompressed directory
    shutil.rmtree(portable_dir)

    # Generate checksums
    sha256_hash = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    txt_path = zip_path.with_suffix(".sha256.txt")
    txt_path.write_text(f"{sha256_hash}  {zip_path.name}\n", encoding="utf-8")

    print(f"[build] SHA-256: {sha256_hash}")
    print(f"[build] Checksum file: {txt_path}")

    return zip_path, txt_path


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[build] Project root: {project_root}")
    print(f"[build] Output directory: {output_dir}")
    print(f"[build] Version: {args.version}")

    if not args.skip_pyinstaller:
        if not args.no_clean:
            for d in [project_root / "build" / "pyinstaller_build"]:
                if d.exists():
                    shutil.rmtree(d)

        executable_dir = build_pyinstaller(project_root)
    else:
        executable_dir = project_root / "build" / "pyinstaller_dist" / "OfflineCorrespondenceSystem"
        if not executable_dir.is_dir():
            print(f"[ERROR] Existing build not found: {executable_dir}")
            print("  Run without --skip-pyinstaller first.")
            sys.exit(1)

    zip_path, txt_path = create_portable_distribution(
        executable_dir=executable_dir,
        output_dir=output_dir,
        version=args.version,
    )

    print(f"\n[build] Portable distribution ready:")
    print(f"  ZIP:    {zip_path}")
    print(f"  SHA256: {txt_path}")


if __name__ == "__main__":
    main()
