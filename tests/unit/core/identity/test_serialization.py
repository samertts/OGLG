from __future__ import annotations

from app.core.identity.models import InstitutionalIdentity, UserIdentity
from app.core.identity.serialization import IdentitySerializer


def test_serialize_institution() -> None:
    from datetime import datetime, timezone
    dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ident = InstitutionalIdentity(
        identity_id="fixed", ministry_id="moh",
        label="Ministry of Health",
        created_at=dt,
    )
    serialized = IdentitySerializer.serialize_institution(ident)
    assert "moh" in serialized
    assert "Ministry of Health" in serialized


def test_serialize_deterministic() -> None:
    from datetime import datetime, timezone
    dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
    i1 = InstitutionalIdentity(
        identity_id="fixed-id", ministry_id="moh",
        created_at=dt,
    )
    i2 = InstitutionalIdentity(
        identity_id="fixed-id", ministry_id="moh",
        created_at=dt,
    )
    s1 = IdentitySerializer.serialize_institution(i1)
    s2 = IdentitySerializer.serialize_institution(i2)
    assert s1 == s2


def test_checksum_consistency() -> None:
    from datetime import datetime, timezone
    dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ident = InstitutionalIdentity(
        identity_id="fixed-id", ministry_id="moh",
        created_at=dt,
    )
    c1 = IdentitySerializer.checksum(ident)
    c2 = IdentitySerializer.checksum(ident)
    assert c1 == c2
    assert len(c1) == 16


def test_serialize_user() -> None:
    from datetime import datetime, timezone
    dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
    user = UserIdentity(
        user_id="fixed", username="jsmith",
        created_at=dt,
    )
    serialized = IdentitySerializer.serialize_user(user)
    assert "jsmith" in serialized
    checksum = IdentitySerializer.checksum(user)
    assert len(checksum) == 16


def test_to_bytes() -> None:
    from datetime import datetime, timezone
    dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ident = InstitutionalIdentity(
        identity_id="fixed", ministry_id="moh",
        created_at=dt,
    )
    data = IdentitySerializer.to_bytes(ident)
    assert isinstance(data, bytes)
    assert b"moh" in data
