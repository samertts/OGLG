from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SignatureMetadata:
    id: str
    user_id: str
    full_name: str
    title: str
    department: str
    signed_at: datetime
    signature_data: str | None = None
    is_digital: bool = False
    is_verified: bool = False
    notes: str = ""

    @staticmethod
    def create(
        user_id: str,
        full_name: str,
        title: str,
        department: str,
        is_digital: bool = False,
    ) -> SignatureMetadata:
        return SignatureMetadata(
            id=str(uuid.uuid4()),
            user_id=user_id,
            full_name=full_name,
            title=title,
            department=department,
            signed_at=datetime.now(),
            is_digital=is_digital,
        )

    @property
    def display_name(self) -> str:
        return f"{self.full_name} ({self.title})"
