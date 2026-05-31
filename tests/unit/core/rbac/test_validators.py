from __future__ import annotations

import pytest

from app.core.rbac.evaluator import PermissionEvaluator
from app.core.rbac.models import Role
from app.core.rbac.validators import AuthorizationError, AuthorizationValidator


def test_authorize_granted() -> None:
    eval = PermissionEvaluator()
    role = Role(name="viewer")
    role.add_permission("letter", "read")
    eval.register_role(role)
    eval.assign_role("user-1", "viewer")
    validator = AuthorizationValidator(eval)
    assert validator.authorize("user-1", "letter", "read")


def test_authorize_denied() -> None:
    eval = PermissionEvaluator()
    validator = AuthorizationValidator(eval)
    assert not validator.authorize("user-1", "letter", "delete")


def test_require_passes() -> None:
    eval = PermissionEvaluator()
    role = Role(name="admin")
    role.add_permission("system", "configure")
    eval.register_role(role)
    eval.assign_role("user-1", "admin")
    validator = AuthorizationValidator(eval)
    validator.require("user-1", "system", "configure")


def test_require_raises() -> None:
    eval = PermissionEvaluator()
    validator = AuthorizationValidator(eval)
    with pytest.raises(AuthorizationError):
        validator.require("user-1", "system", "configure")


def test_authorization_metadata() -> None:
    eval = PermissionEvaluator()
    role = Role(name="viewer")
    role.add_permission("letter", "read")
    eval.register_role(role)
    eval.assign_role("user-1", "viewer")
    validator = AuthorizationValidator(eval)
    meta = validator.authorization_metadata("user-1", "letter", "read")
    assert meta["granted"] is True
    assert meta["user_id"] == "user-1"
    assert "viewer" in meta["roles"]
