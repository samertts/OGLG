from __future__ import annotations

from typing import Any

from app.core.rbac.evaluator import PermissionEvaluator
from app.core.rbac.models import Action, Resource


class AuthorizationValidator:
    """Deterministic authorization validation with audit metadata."""

    def __init__(self, evaluator: PermissionEvaluator) -> None:
        self._evaluator = evaluator

    def authorize(
        self,
        user_id: str,
        resource: Resource,
        action: Action,
    ) -> bool:
        return self._evaluator.has_permission(user_id, resource, action)

    def require(
        self,
        user_id: str,
        resource: Resource,
        action: Action,
    ) -> None:
        if not self.authorize(user_id, resource, action):
            raise AuthorizationError(
                f"User {user_id} lacks '{action}' on '{resource}'"
            )

    def authorization_metadata(
        self,
        user_id: str,
        resource: Resource,
        action: Action,
    ) -> dict[str, Any]:
        granted = self.authorize(user_id, resource, action)
        return {
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "granted": granted,
            "roles": [
                r.name
                for r in self._evaluator.user_roles(user_id)
            ],
        }


class AuthorizationError(Exception):
    """Raised when authorization is denied."""
