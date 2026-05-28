from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentReference:
    prefix: str
    year: int
    sequence: int

    def __str__(self) -> str:
        return f"{self.prefix}-{self.year}-{self.sequence:06d}"

    @staticmethod
    def parse(value: str) -> DocumentReference:
        parts = value.split("-")
        if len(parts) != 3:
            raise ValueError(f"Invalid document reference format: {value}")
        return DocumentReference(parts[0], int(parts[1]), int(parts[2]))

    @staticmethod
    def is_valid(value: str) -> bool:
        return bool(re.match(r"^[A-Za-z0-9]+-\d{4}-\d{6}$", value))

    @staticmethod
    def is_valid_format(value: str) -> bool:
        return DocumentReference.is_valid(value)

    @property
    def display(self) -> str:
        return str(self)
