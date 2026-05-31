from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

UserId = str
MinistryId = str
DepartmentId = str
BranchId = str
WorkstationId = str


class IdentityType(Enum):
    MINISTRY = "ministry"
    DEPARTMENT = "department"
    BRANCH = "branch"
    WORKSTATION = "workstation"
    USER = "user"
    SYSTEM = "system"


@dataclass(frozen=True)
class InstitutionalIdentity:
    identity_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    identity_type: IdentityType = IdentityType.SYSTEM
    ministry_id: MinistryId = ""
    department_id: DepartmentId = ""
    branch_id: BranchId = ""
    workstation_id: WorkstationId = ""
    label: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def hierarchy(self) -> list[str]:
        parts: list[str] = []
        if self.ministry_id:
            parts.append(f"ministry:{self.ministry_id}")
        if self.department_id:
            parts.append(f"department:{self.department_id}")
        if self.branch_id:
            parts.append(f"branch:{self.branch_id}")
        if self.workstation_id:
            parts.append(f"workstation:{self.workstation_id}")
        return parts

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity_id": self.identity_id,
            "identity_type": self.identity_type.value,
            "ministry_id": self.ministry_id,
            "department_id": self.department_id,
            "branch_id": self.branch_id,
            "workstation_id": self.workstation_id,
            "label": self.label,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class UserIdentity:
    user_id: UserId = field(default_factory=lambda: uuid.uuid4().hex)
    username: str = ""
    full_name: str = ""
    institution: InstitutionalIdentity = field(
        default_factory=InstitutionalIdentity
    )
    roles: list[str] = field(default_factory=list)
    active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "full_name": self.full_name,
            "institution": self.institution.to_dict(),
            "roles": list(self.roles),
            "active": self.active,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
