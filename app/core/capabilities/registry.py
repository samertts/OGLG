from __future__ import annotations

import threading
from typing import Any

from app.core.capabilities.contracts import (
    CapabilityContract,
    CapabilityVersion,
    DependencySpec,
)


class CapabilityRegistry:
    """Subsystem capability registry with discovery and validation."""

    def __init__(self) -> None:
        self._capabilities: dict[str, CapabilityContract] = {}
        self._lock = threading.RLock()

    def register(self, contract: CapabilityContract) -> None:
        with self._lock:
            if contract.name in self._capabilities:
                raise ValueError(
                    f"Capability already registered: {contract.name}"
                )
            for dep in contract.dependencies:
                if not dep.optional and dep.name not in self._capabilities:
                    resolved = self._resolve_dependency(dep)
                    if resolved is None:
                        raise ValueError(
                            f"Unsatisfied dependency: {dep.name} >= {dep.min_version}"
                        )
            self._capabilities[contract.name] = contract

    def _resolve_dependency(
        self, dep: DependencySpec
    ) -> CapabilityContract | None:
        existing = self._capabilities.get(dep.name)
        if existing is None:
            return None
        if existing.version < dep.min_version:
            return None
        return existing

    def unregister(self, name: str) -> None:
        with self._lock:
            self._capabilities.pop(name, None)

    def get(self, name: str) -> CapabilityContract | None:
        return self._capabilities.get(name)

    def discover(self, prefix: str = "") -> list[CapabilityContract]:
        with self._lock:
            if not prefix:
                return list(self._capabilities.values())
            return [
                c for c in self._capabilities.values()
                if c.name.startswith(prefix)
            ]

    def has(self, name: str) -> bool:
        return name in self._capabilities

    def validate_dependencies(self, name: str) -> bool:
        contract = self.get(name)
        if contract is None:
            return False
        for dep in contract.dependencies:
            resolved = self._resolve_dependency(dep)
            if resolved is None and not dep.optional:
                return False
        return True

    def version_of(self, name: str) -> CapabilityVersion | None:
        contract = self.get(name)
        return contract.version if contract else None

    @property
    def count(self) -> int:
        return len(self._capabilities)

    def state(self) -> dict[str, Any]:
        with self._lock:
            return {
                "count": self.count,
                "capabilities": [
                    {
                        "name": c.name,
                        "version": c.version,
                        "description": c.description,
                        "dependencies": [
                            {"name": d.name, "min_version": d.min_version, "optional": d.optional}
                            for d in c.dependencies
                        ],
                    }
                    for c in self._capabilities.values()
                ],
            }
