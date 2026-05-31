#!/usr/bin/env python3
"""Offline verification bundle — verify release artifacts without internet."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.build.manifest import BuildManifest
from app.build.verifier import BuildVerifier


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verify release artifacts offline")
    p.add_argument("--manifest", required=True, type=Path, help="Path to manifest.json")
    p.add_argument("--artifact-dir", required=True, type=Path,
                   help="Directory with release artifacts")
    return p.parse_args(argv)


def main() -> None:
    args = parse_args()
    if not args.manifest.exists():
        print(f"Manifest not found: {args.manifest}")
        sys.exit(1)
    if not args.artifact_dir.is_dir():
        print(f"Artifact directory not found: {args.artifact_dir}")
        sys.exit(1)

    manifest = BuildManifest.from_file(args.manifest)
    verifier = BuildVerifier(manifest)
    result = verifier.verify_all(args.artifact_dir)

    print(f"Verification: {'PASS' if result.passed else 'FAIL'}")
    print(f"  Verified: {result.verified_count}/{len(manifest.entries)}")
    if result.missing:
        print(f"  Missing: {len(result.missing)}")
        for m in result.missing[:5]:
            print(f"    - {m}")
    if result.mismatched:
        print(f"  Mismatched: {len(result.mismatched)}")
        for m in result.mismatched[:5]:
            print(f"    - {m}")
    if result.extra:
        print(f"  Extra: {len(result.extra)}")
        for e in result.extra[:5]:
            print(f"    - {e}")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
