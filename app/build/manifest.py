from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class BuildManifestEntry:
    path: str
    sha256: str
    size_bytes: int


@dataclass
class BuildManifest:
    version: str
    app_name: str
    build_timestamp: str
    python_version: str
    entries: list[BuildManifestEntry] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    def add_entry(self, path: str, data: bytes) -> BuildManifestEntry:
        sha256 = hashlib.sha256(data).hexdigest()
        entry = BuildManifestEntry(
            path=path,
            sha256=sha256,
            size_bytes=len(data),
        )
        self.entries.append(entry)
        return entry

    def add_file(self, file_path: Path, archive_prefix: str = "") -> BuildManifestEntry:
        data = file_path.read_bytes()
        relative = str(file_path)
        if archive_prefix:
            relative = f"{archive_prefix}/{file_path.name}"
        return self.add_entry(relative, data)

    def to_json(self) -> str:
        return json.dumps(
            {
                "version": self.version,
                "app_name": self.app_name,
                "build_timestamp": self.build_timestamp,
                "python_version": self.python_version,
                "entries": sorted(
                    [asdict(e) for e in self.entries],
                    key=lambda x: x["path"],
                ),
                "metadata": dict(sorted(self.metadata.items())),
            },
            indent=2,
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, data: str) -> BuildManifest:
        raw = json.loads(data)
        manifest = cls(
            version=raw["version"],
            app_name=raw["app_name"],
            build_timestamp=raw["build_timestamp"],
            python_version=raw["python_version"],
            entries=[BuildManifestEntry(**e) for e in raw["entries"]],
            metadata=raw.get("metadata", {}),
        )
        return manifest

    def to_file(self, path: Path) -> None:
        path.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def from_file(cls, path: Path) -> BuildManifest:
        return cls.from_json(path.read_text(encoding="utf-8"))

    def deterministic_id(self) -> str:
        h = hashlib.sha256()
        for entry in sorted(self.entries, key=lambda e: e.path):
            h.update(f"{entry.path}:{entry.sha256}:{entry.size_bytes}\n".encode())
        return h.hexdigest()

    @property
    def total_size_bytes(self) -> int:
        return sum(e.size_bytes for e in self.entries)

    @property
    def file_count(self) -> int:
        return len(self.entries)
