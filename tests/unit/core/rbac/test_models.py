from __future__ import annotations

from app.core.rbac.models import Permission, Role


def test_permission_str() -> None:
    p = Permission(resource="letter", action="read")
    assert str(p) == "letter:read"


def test_role_add_permission() -> None:
    role = Role(name="editor")
    role.add_permission("letter", "create")
    role.add_permission("letter", "read")
    assert len(role.permissions) == 2
    assert role.has_permission("letter", "create")
    assert not role.has_permission("letter", "delete")


def test_role_inheritance() -> None:
    base = Role(name="viewer")
    base.add_permission("letter", "read")

    admin = Role(name="admin", parents=["viewer"])
    admin.add_permission("letter", "delete")

    assert base.has_permission("letter", "read")
    assert admin.has_permission("letter", "delete")
