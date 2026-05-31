from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

NodeId = str
InstitutionId = str
BranchId = str
DepartmentId = str


class NodeRole(Enum):
    STANDALONE = "standalone"
    HEADQUARTERS = "headquarters"
    BRANCH = "branch"
    DEPARTMENT = "department"
    FIELD = "field"
    LABORATORY = "laboratory"


@dataclass(frozen=True)
class NodeAddress:
    hostname: str = ""
    port: int = 0
    path: str = ""

    def is_local(self) -> bool:
        return not self.hostname or self.hostname in (
            "localhost", "127.0.0.1", "::1"
        )


@dataclass
class FederationNode:
    node_id: NodeId = field(default_factory=lambda: uuid.uuid4().hex)
    institution_id: InstitutionId = ""
    branch_id: BranchId = ""
    department_id: DepartmentId = ""
    role: NodeRole = NodeRole.STANDALONE
    label: str = ""
    address: NodeAddress = field(default_factory=NodeAddress)
    version: str = "1.0.0"
    public_key_hash: str = ""
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def identity(self) -> dict[str, str]:
        return {
            "node_id": self.node_id,
            "institution_id": self.institution_id,
            "branch_id": self.branch_id,
            "department_id": self.department_id,
            "role": self.role.value,
            "version": self.version,
        }

    def is_federated(self) -> bool:
        return bool(self.institution_id and self.node_id)

    def __hash__(self) -> int:
        return hash(self.node_id)
