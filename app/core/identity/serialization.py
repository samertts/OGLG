from __future__ import annotations

import hashlib
import json

from app.core.identity.models import InstitutionalIdentity, UserIdentity


class IdentitySerializer:
    """Deterministic identity serialization with integrity checks."""

    @staticmethod
    def serialize_institution(
        identity: InstitutionalIdentity,
    ) -> str:
        return json.dumps(
            identity.to_dict(),
            sort_keys=True,
            ensure_ascii=True,
        )

    @staticmethod
    def serialize_user(identity: UserIdentity) -> str:
        return json.dumps(
            identity.to_dict(),
            sort_keys=True,
            ensure_ascii=True,
        )

    @staticmethod
    def checksum(identity: InstitutionalIdentity | UserIdentity) -> str:
        if isinstance(identity, InstitutionalIdentity):
            raw = IdentitySerializer.serialize_institution(identity)
        else:
            raw = IdentitySerializer.serialize_user(identity)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    @staticmethod
    def to_bytes(
        identity: InstitutionalIdentity | UserIdentity,
    ) -> bytes:
        if isinstance(identity, InstitutionalIdentity):
            return IdentitySerializer.serialize_institution(
                identity
            ).encode("utf-8")
        return IdentitySerializer.serialize_user(identity).encode(
            "utf-8"
        )
