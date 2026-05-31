from __future__ import annotations

import threading
from typing import Any

from app.core.rbac.models import Action, Permission, Resource, Role, RoleAssignment


class PermissionEvaluator:
    """Deterministic permission evaluation with role inheritance."""

    def __init__(self) -> None:
        self._roles: dict[str, Role] = {}
        self._assignments: dict[str, list[RoleAssignment]] = {}
        self._lock = threading.RLock()

    def register_role(self, role: Role) -> None:
        with self._lock:
            self._roles[role.name] = role

    def unregister_role(self, role_name: str) -> None:
        with self._lock:
            self._roles.pop(role_name, None)

    def assign_role(
        self, user_id: str, role_name: str, **kwargs: Any
    ) -> RoleAssignment:
        assignment = RoleAssignment(
            user_id=user_id,
            role_name=role_name,
            institution_filter=kwargs,
        )
        with self._lock:
            if user_id not in self._assignments:
                self._assignments[user_id] = []
            self._assignments[user_id].append(assignment)
        return assignment

    def unassign_role(
        self, user_id: str, role_name: str
    ) -> bool:
        with self._lock:
            assignments = self._assignments.get(user_id, [])
            before = len(assignments)
            self._assignments[user_id] = [
                a for a in assignments if a.role_name != role_name
            ]
            return len(self._assignments[user_id]) < before

    def user_roles(self, user_id: str) -> list[Role]:
        with self._lock:
            assignments = self._assignments.get(user_id, [])
            roles: list[Role] = []
            seen: set[str] = set()
            for assignment in assignments:
                role = self._roles.get(assignment.role_name)
                if role is not None:
                    self._collect_role(role, roles, seen)
            return roles

    def _collect_role(
        self, role: Role, collected: list[Role], seen: set[str]
    ) -> None:
        if role.name in seen:
            return
        seen.add(role.name)
        collected.append(role)
        for parent_name in role.parents:
            parent = self._roles.get(parent_name)
            if parent is not None:
                self._collect_role(parent, collected, seen)

    def has_permission(
        self,
        user_id: str,
        resource: Resource,
        action: Action,
    ) -> bool:
        roles = self.user_roles(user_id)
        target = Permission(resource=resource, action=action)
        for role in roles:
            if target in role.permissions:
                return True
        return False

    def permissions_for(self, user_id: str) -> set[Permission]:
        roles = self.user_roles(user_id)
        result: set[Permission] = set()
        for role in roles:
            result.update(role.permissions)
        return result

    def state(self) -> dict[str, Any]:
        with self._lock:
            return {
                "roles": list(self._roles.keys()),
                "users_with_assignments": len(self._assignments),
            }
