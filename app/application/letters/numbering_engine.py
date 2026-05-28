from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import Any

from loguru import logger


class NumberingEngine:
    def __init__(self, sequence_provider: Any) -> None:
        self._provider = sequence_provider
        self._lock = Lock()

    def generate(
        self,
        department_code: str,
        year: int | None = None,
    ) -> str:
        if not department_code or not department_code.strip():
            raise ValueError("Department code cannot be empty")
        if len(department_code) > 10:
            raise ValueError(f"Department code too long: {department_code}")
        year = year or datetime.now().year
        with self._lock:
            sequence = self._provider.next_sequence(department_code, year)
            number = f"{department_code}-{year}-{sequence:06d}"
            logger.debug(f"Generated letter number: {number}")
            return number

    def generate_batch(
        self,
        department_code: str,
        count: int,
        year: int | None = None,
    ) -> list[str]:
        if count < 1:
            raise ValueError("Count must be at least 1")
        if count > 1000:
            raise ValueError("Batch count cannot exceed 1000")
        year = year or datetime.now().year
        numbers: list[str] = []
        with self._lock:
            start = self._provider.next_sequence(department_code, year, count)
            for i in range(count):
                seq = start + i
                numbers.append(f"{department_code}-{year}-{seq:06d}")
            logger.debug(f"Generated batch of {count} numbers for {department_code}")
            return numbers

    def parse_number(self, number: str) -> tuple[str, int, int]:
        try:
            parts = number.split("-")
            if len(parts) != 3:
                raise ValueError(f"Invalid number format: {number}")
            return parts[0], int(parts[1]), int(parts[2])
        except (ValueError, IndexError) as exc:
            raise ValueError(f"Invalid number format: {number}") from exc

    def validate_number(self, number: str) -> bool:
        import re

        return bool(re.match(r"^[A-Za-z0-9]+-\d{4}-\d{6}$", number))
