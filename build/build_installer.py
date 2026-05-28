#!/usr/bin/env python3
"""Installer build orchestrator.

Builds the PyInstaller executable and then compiles the Inno Setup
installer script into a Windows Setup executable.

Usage:
    python build/build_installer.py [--version 1.0.0] [--output-dir ./dist]
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Windows installer for the Correspondence System",
    )
    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Version string for the installer (default: 1.0.0)",
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
        "--iscc-path",
        default="iscc",
        help="Path to Inno Setup Compiler (iscc.exe) — default: 'iscc'",
    )
    return parser.parse_args(argv)


def build_pyinstaller(project_root: Path) -> Path:
    """Run PyInstaller and return the output directory path."""
    spec_path = project_root / "build" / "oglg.spec"
    build_dir = project_root / "build" / "pyinstaller_build"
    dist_dir = project_root / "build" / "pyinstaller_dist"

    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    print(f"[installer] Running PyInstaller: {spec_path}")
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

    print(f"[installer] PyInstaller output: {dist_dir}")
    return dist_dir / "OfflineCorrespondenceSystem"


def compile_installer(
    project_root: Path,
    executable_dir: Path,
    output_dir: Path,
    version: str,
    iscc_path: str,
) -> Path:
    """Compile the Inno Setup script into an installer executable.

    Args:
        project_root: Project root directory.
        executable_dir: PyInstaller one-folder output directory.
        output_dir: Destination for the installer executable.
        version: Version string.
        iscc_path: Path to iscc.exe.

    Returns:
        Path to the generated installer executable.
    """
    iss_path = project_root / "build" / "setup.iss"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Inno Setup reads environment variables for its #define directives
    env = os.environ.copy()
    env["APP_VERSION"] = version
    env["SOURCE_DIR"] = str(executable_dir.resolve())
    env["OUTPUT_DIR"] = str(output_dir.resolve())
    env["PROJECT_ROOT"] = str(project_root.resolve())

    print(f"[installer] Compiling Inno Setup script: {iss_path}")
    result = subprocess.run(
        [iscc_path, str(iss_path)],
        env=env,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"[ERROR] Inno Setup compilation failed:\n{result.stdout}\n{result.stderr}")
        sys.exit(1)

    print(f"[installer] Inno Setup output:\n{result.stdout}")

    # Find generated installer
    installer_name = f"OfflineCorrespondenceSystem_Setup_{version}.exe"
    installer_path = output_dir / installer_name

    if not installer_path.exists():
        print(f"[ERROR] Installer not found at expected path: {installer_path}")
        sys.exit(1)

    print(f"[installer] Installer created: {installer_path}")

    # Generate checksum
    sha256_hash = hashlib.sha256(installer_path.read_bytes()).hexdigest()
    txt_path = installer_path.with_suffix(".exe.sha256.txt")
    txt_path.write_text(f"{sha256_hash}  {installer_path.name}\n", encoding="utf-8")
    print(f"[installer] SHA-256: {sha256_hash}")

    return installer_path


def main() -> None:
    args = parse_args()
    project_root = Path(__file__).resolve().parent.parent
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[installer] Project root: {project_root}")
    print(f"[installer] Output directory: {output_dir}")
    print(f"[installer] Version: {args.version}")

    if not args.skip_pyinstaller:
        executable_dir = build_pyinstaller(project_root)
    else:
        executable_dir = project_root / "build" / "pyinstaller_dist" / "OfflineCorrespondenceSystem"
        if not executable_dir.is_dir():
            print(f"[ERROR] Existing build not found: {executable_dir}")
            sys.exit(1)

    compile_installer(
        project_root=project_root,
        executable_dir=executable_dir,
        output_dir=output_dir,
        version=args.version,
        iscc_path=args.iscc_path,
    )

    print(f"\n[installer] Installer build complete.")
    print(f"  Output: {output_dir}")


if __name__ == "__main__":
    main()
