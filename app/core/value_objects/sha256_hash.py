from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class SHA256Hash:
    """SHA-256 hash value object for content integrity verification."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Hash value must be a non-empty string")
        if len(self.value) != 64:
            raise ValueError(f"SHA-256 hash must be 64 hex characters, got {len(self.value)}")
        int(self.value, 16)  # validate hex

    @classmethod
    def compute(cls, data: bytes) -> SHA256Hash:
        return cls(value=hashlib.sha256(data).hexdigest())

    @classmethod
    def compute_from_string(cls, text: str, encoding: str = "utf-8") -> SHA256Hash:
        return cls.compute(text.encode(encoding))

    def matches(self, data: bytes) -> bool:
        return self.value == hashlib.sha256(data).hexdigest()

    def __str__(self) -> str:
        return self.value
