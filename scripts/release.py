#!/usr/bin/env python3
"""GitHub release preparation script.

Generates release artifacts, checksums, and release notes
for GitHub Releases.

Usage:
    python scripts/release.py --version 1.0.0 [--dist-dir ./dist]
"""

from __future__ import annotations

import argparse
import hashlib
from datetime import datetime
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare GitHub release artifacts",
    )
    parser.add_argument("--version", required=True, help="Version string (e.g. 1.0.0)")
    parser.add_argument("--dist-dir", default="./dist", help="Distribution artifacts directory")
    parser.add_argument(
        "--output", default="./RELEASE_NOTES.md", help="Output path for release notes"
    )
    return parser.parse_args(argv)


def generate_release_notes(version: str, dist_dir: Path, output_path: Path) -> None:
    """Generate GitHub release notes with checksums and artifact listing.

    Args:
        version: Version string.
        dist_dir: Directory containing release artifacts.
        output_path: Path to write the release notes markdown.
    """
    artifacts = sorted(dist_dir.iterdir()) if dist_dir.is_dir() else []

    lines: list[str] = []
    lines.append(f"## v{version}")
    lines.append("")
    lines.append(f"Release date: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append("")
    lines.append("### Downloads")
    lines.append("")

    checksums: list[str] = []
    for artifact in artifacts:
        if artifact.suffix in (".zip", ".exe"):
            sha256 = hashlib.sha256(artifact.read_bytes()).hexdigest()
            size_kb = artifact.stat().st_size / 1024
            lines.append(f"- `{artifact.name}` ({size_kb:.0f} KB)")
            checksums.append(f"  - SHA-256: `{sha256}`")

    if checksums:
        lines.append("")
        lines.append("### Checksums")
        lines.append("")
        lines.extend(checksums)

    lines.append("")
    lines.append("### Migration Notes")
    lines.append("")
    lines.append("- Back up your database before upgrading.")
    lines.append("- Schema migrations run automatically on first startup.")
    lines.append("- Archives and backups are preserved during upgrades.")
    lines.append("")
    lines.append("### Compatibility")
    lines.append("")
    lines.append("- Windows 7, 8, 10, 11")
    lines.append("- Fully offline operation")
    lines.append("- Portable and installed modes")

    content = "\n".join(lines)
    output_path.write_text(content, encoding="utf-8")
    print(f"Release notes written to {output_path}")
    print(f"  {len(lines)} lines, {len(artifacts)} artifacts found")


def main() -> None:
    args = parse_args()
    dist_dir = Path(args.dist_dir).resolve()
    output_path = Path(args.output).resolve()

    generate_release_notes(
        version=args.version,
        dist_dir=dist_dir,
        output_path=output_path,
    )


if __name__ == "__main__":
    main()
