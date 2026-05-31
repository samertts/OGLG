from __future__ import annotations

from app.core.rbac.evaluator import PermissionEvaluator
from app.core.rbac.models import Role


def test_evaluator_direct_permission() -> None:
    eval = PermissionEvaluator()
    role = Role(name="viewer")
    role.add_permission("letter", "read")
    eval.register_role(role)
    eval.assign_role("user-1", "viewer")
    assert eval.has_permission("user-1", "letter", "read")
    assert not eval.has_permission("user-1", "letter", "delete")


def test_evaluator_inherited_permission() -> None:
    eval = PermissionEvaluator()
    base = Role(name="base")
    base.add_permission("letter", "read")
    extended = Role(name="extended", parents=["base"])
    extended.add_permission("letter", "write")
    eval.register_role(base)
    eval.register_role(extended)
    eval.assign_role("user-1", "extended")
    assert eval.has_permission("user-1", "letter", "read")
    assert eval.has_permission("user-1", "letter", "write")


def test_evaluator_multi_level_inheritance() -> None:
    eval = PermissionEvaluator()
    r1 = Role(name="level1")
    r1.add_permission("a", "read")
    r2 = Role(name="level2", parents=["level1"])
    r2.add_permission("a", "write")
    r3 = Role(name="level3", parents=["level2"])
    r3.add_permission("a", "delete")
    eval.register_role(r1)
    eval.register_role(r2)
    eval.register_role(r3)
    eval.assign_role("user-1", "level3")
    assert eval.has_permission("user-1", "a", "read")
    assert eval.has_permission("user-1", "a", "write")
    assert eval.has_permission("user-1", "a", "delete")


def test_evaluator_unassign() -> None:
    eval = PermissionEvaluator()
    role = Role(name="viewer")
    role.add_permission("letter", "read")
    eval.register_role(role)
    eval.assign_role("user-1", "viewer")
    assert eval.has_permission("user-1", "letter", "read")
    eval.unassign_role("user-1", "viewer")
    assert not eval.has_permission("user-1", "letter", "read")


def test_evaluator_multiple_roles() -> None:
    eval = PermissionEvaluator()
    r1 = Role(name="role_a")
    r1.add_permission("x", "read")
    r2 = Role(name="role_b")
    r2.add_permission("y", "write")
    eval.register_role(r1)
    eval.register_role(r2)
    eval.assign_role("user-1", "role_a")
    eval.assign_role("user-1", "role_b")
    assert eval.has_permission("user-1", "x", "read")
    assert eval.has_permission("user-1", "y", "write")


def test_evaluator_permissions_for() -> None:
    eval = PermissionEvaluator()
    role = Role(name="viewer")
    role.add_permission("letter", "read")
    role.add_permission("letter", "list")
    eval.register_role(role)
    eval.assign_role("user-1", "viewer")
    perms = eval.permissions_for("user-1")
    assert len(perms) == 2


def test_evaluator_state() -> None:
    eval = PermissionEvaluator()
    role = Role(name="test")
    eval.register_role(role)
    eval.assign_role("user-1", "test")
    state = eval.state()
    assert "test" in state["roles"]
    assert state["users_with_assignments"] == 1
