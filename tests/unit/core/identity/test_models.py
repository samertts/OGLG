from __future__ import annotations

from app.core.identity.models import (
    IdentityType,
    InstitutionalIdentity,
    UserIdentity,
)


def test_institutional_identity_defaults() -> None:
    ident = InstitutionalIdentity()
    assert ident.identity_id is not None
    assert ident.identity_type == IdentityType.SYSTEM


def test_institutional_identity_hierarchy() -> None:
    ident = InstitutionalIdentity(
        ministry_id="moh",
        department_id="hr",
        branch_id="central",
    )
    hierarchy = ident.hierarchy()
    assert hierarchy == [
        "ministry:moh",
        "department:hr",
        "branch:central",
    ]


def test_institutional_identity_to_dict() -> None:
    ident = InstitutionalIdentity(
        identity_type=IdentityType.MINISTRY,
        ministry_id="moh",
        label="Ministry of Health",
    )
    d = ident.to_dict()
    assert d["ministry_id"] == "moh"
    assert d["identity_type"] == "ministry"
    assert d["label"] == "Ministry of Health"


def test_user_identity() -> None:
    inst = InstitutionalIdentity(
        ministry_id="moh", department_id="it"
    )
    user = UserIdentity(
        username="jsmith",
        full_name="John Smith",
        institution=inst,
        roles=["admin", "editor"],
    )
    assert user.user_id is not None
    assert user.username == "jsmith"
    assert "admin" in user.roles
    assert user.active


def test_user_identity_to_dict() -> None:
    user = UserIdentity(
        username="jsmith",
        full_name="John Smith",
    )
    d = user.to_dict()
    assert d["username"] == "jsmith"
    assert d["full_name"] == "John Smith"
    assert d["active"] is True
