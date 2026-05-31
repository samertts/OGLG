from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CapabilityVersion = str


@dataclass(frozen=True)
class DependencySpec:
    name: str
    min_version: CapabilityVersion = "0.0.0"
    optional: bool = False


@dataclass(frozen=True)
class CapabilityContract:
    name: str
    version: CapabilityVersion
    description: str = ""
    dependencies: list[DependencySpec] = field(default_factory=list)
    provides: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def requires(self, dep_name: str) -> bool:
        return any(d.name == dep_name for d in self.dependencies)
