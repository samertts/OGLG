from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentId:
    """UUID-based document identifier value object."""

    value: uuid.UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, uuid.UUID):
            raise ValueError("DocumentId must be a UUID")

    @classmethod
    def new(cls) -> DocumentId:
        return cls(value=uuid.uuid4())

    @classmethod
    def from_string(cls, text: str) -> DocumentId:
        return cls(value=uuid.UUID(text))

    def __str__(self) -> str:
        return str(self.value)
