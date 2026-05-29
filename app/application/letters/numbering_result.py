from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class NumberingResult:
    success: bool
    number: str
    prefix: str
    year: int
    sequence: int
    timestamp: datetime
    error: str | None = None
    error_code: str | None = None
    _metadata: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @staticmethod
    def ok(
        number: str,
        prefix: str,
        year: int,
        sequence: int,
        metadata: dict[str, Any] | None = None,
    ) -> NumberingResult:
        return NumberingResult(
            success=True,
            number=number,
            prefix=prefix,
            year=year,
            sequence=sequence,
            timestamp=datetime.now(),
            _metadata=metadata or {},
        )

    @staticmethod
    def fail(
        error: str,
        error_code: str | None = None,
        number: str = "",
        prefix: str = "",
        year: int = 0,
        sequence: int = 0,
    ) -> NumberingResult:
        return NumberingResult(
            success=False,
            number=number,
            prefix=prefix,
            year=year,
            sequence=sequence,
            timestamp=datetime.now(),
            error=error,
            error_code=error_code,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "number": self.number,
            "prefix": self.prefix,
            "year": self.year,
            "sequence": self.sequence,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
            "error_code": self.error_code,
        }

    @property
    def is_ok(self) -> bool:
        return self.success

    @property
    def is_error(self) -> bool:
        return not self.success and self.error is not None


__all__ = [
    "NumberingResult",
]
