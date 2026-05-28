from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class LetterNumber:
    """Official government letter number value object.

    Format: {PREFIX}-{YEAR}-{SEQUENCE:04d}
    Example: MOH-2026-0042
    """

    prefix: str
    year: int
    sequence: int

    PATTERN = re.compile(r"^([A-Za-z0-9]{2,5})-(\d{4})-(\d{4})$")

    def format(self) -> str:
        return f"{self.prefix}-{self.year}-{self.sequence:04d}"

    @classmethod
    def parse(cls, value: str) -> LetterNumber:
        if not value or not isinstance(value, str):
            raise ValueError(f"Invalid letter number format: {value}")
        match = cls.PATTERN.match(value.strip())
        if not match:
            raise ValueError(f"Letter number does not match pattern: {value}")
        return cls(
            prefix=match.group(1).upper(),
            year=int(match.group(2)),
            sequence=int(match.group(3)),
        )

    @classmethod
    def create(cls, prefix: str, year: int, sequence: int) -> LetterNumber:
        if not prefix or len(prefix) < 2 or len(prefix) > 5:
            raise ValueError(f"Invalid prefix: {prefix}")
        if year < 2000 or year > 2100:
            raise ValueError(f"Invalid year: {year}")
        if sequence < 1 or sequence > 9999:
            raise ValueError(f"Invalid sequence: {sequence}")
        return cls(prefix=prefix.upper(), year=year, sequence=sequence)

    def __str__(self) -> str:
        return self.format()
