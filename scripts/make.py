#!/usr/bin/env python3
"""Script runner for common development and build tasks.

Provides convenience commands for building, testing, and validation.

Usage:
    python scripts/make.py build-portable --version 1.0.0
    python scripts/make.py build-installer --version 1.0.0
    python scripts/make.py validate --path ./dist/portable.zip
    python scripts/make.py test
    python scripts/make.py lint
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def cmd_build_portable(args: argparse.Namespace) -> int:
    return subprocess.call(
        [sys.executable, str(PROJECT_ROOT / "build" / "build_portable.py"),
         "--version", args.version,
         "--output-dir", args.output_dir],
    )


def cmd_build_installer(args: argparse.Namespace) -> int:
    return subprocess.call(
        [sys.executable, str(PROJECT_ROOT / "build" / "build_installer.py"),
         "--version", args.version,
         "--output-dir", args.output_dir],
    )


def cmd_validate(args: argparse.Namespace) -> int:
    cmd = [sys.executable, str(PROJECT_ROOT / "build" / "validate_build.py")]
    if args.path:
        p = Path(args.path)
        if p.suffix == ".zip":
            cmd.extend(["--zip", str(p)])
        else:
            cmd.extend(["--build-dir", str(p)])
    if args.strict:
        cmd.append("--strict")
    return subprocess.call(cmd)


def cmd_test(args: argparse.Namespace) -> int:
    cmd = [sys.executable, "-m", "pytest"]
    if args.coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])
    if args.verbose:
        cmd.append("-v")
    if args.paths:
        cmd.extend(args.paths)
    return subprocess.call(cmd)


def cmd_lint(_args: argparse.Namespace) -> int:
    return subprocess.call(
        [sys.executable, "-m", "ruff", "check", "app", "tests", "build", "scripts"]
    )


def cmd_release(args: argparse.Namespace) -> int:
    return subprocess.call(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "release.py"),
         "--version", args.version,
         "--dist-dir", args.output_dir],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Development task runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # build-portable
    p = subparsers.add_parser("build-portable", help="Build portable ZIP distribution")
    p.add_argument("--version", default="1.0.0")
    p.add_argument("--output-dir", default="./dist")
    p.set_defaults(func=cmd_build_portable)

    # build-installer
    p = subparsers.add_parser("build-installer", help="Build Windows installer")
    p.add_argument("--version", default="1.0.0")
    p.add_argument("--output-dir", default="./dist")
    p.set_defaults(func=cmd_build_installer)

    # validate
    p = subparsers.add_parser("validate", help="Validate build artifacts")
    p.add_argument("--path", required=True, help="Path to build dir or ZIP")
    p.add_argument("--strict", action="store_true")
    p.set_defaults(func=cmd_validate)

    # test
    p = subparsers.add_parser("test", help="Run tests")
    p.add_argument("--coverage", action="store_true")
    p.add_argument("--verbose", "-v", action="store_true")
    p.add_argument("paths", nargs="*", default=[])
    p.set_defaults(func=cmd_test)

    # lint
    p = subparsers.add_parser("lint", help="Run linter")
    p.set_defaults(func=cmd_lint)

    # release
    p = subparsers.add_parser("release", help="Prepare release notes")
    p.add_argument("--version", required=True)
    p.add_argument("--output-dir", default="./dist")
    p.set_defaults(func=cmd_release)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
