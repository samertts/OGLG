from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

Resource = str
Action = str


@dataclass(frozen=True)
class Permission:
    resource: Resource
    action: Action

    def __str__(self) -> str:
        return f"{self.resource}:{self.action}"


@dataclass(frozen=True)
class RoleInheritance:
    parent_role: str
    child_role: str

    def __str__(self) -> str:
        return f"{self.child_role} -> {self.parent_role}"


@dataclass
class Role:
    role_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    name: str = ""
    description: str = ""
    permissions: set[Permission] = field(default_factory=set)
    parents: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_permission(self, resource: Resource, action: Action) -> None:
        self.permissions.add(Permission(resource=resource, action=action))

    def has_permission(self, resource: Resource, action: Action) -> bool:
        return Permission(resource=resource, action=action) in self.permissions


@dataclass
class RoleAssignment:
    assignment_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    user_id: str = ""
    role_name: str = ""
    institution_filter: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
