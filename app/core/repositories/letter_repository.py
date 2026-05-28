from __future__ import annotations

from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from app.core.entities.letter import Letter


class LetterRepository(Protocol):
    """Repository interface for Letter aggregate."""

    @abstractmethod
    def find_by_id(self, id: UUID) -> Letter | None: ...

    @abstractmethod
    def find_by_number(self, number: str) -> Letter | None: ...

    @abstractmethod
    def find_by_department(
        self, department_id: UUID, offset: int = 0, limit: int = 50
    ) -> list[Letter]: ...

    @abstractmethod
    def find_by_date_range(
        self, start: str | None, end: str | None, offset: int = 0, limit: int = 50
    ) -> list[Letter]: ...

    @abstractmethod
    def find_archived(self, offset: int = 0, limit: int = 50) -> list[Letter]: ...

    @abstractmethod
    def find_deleted(self, offset: int = 0, limit: int = 50) -> list[Letter]: ...

    @abstractmethod
    def search(self, query: str, offset: int = 0, limit: int = 50) -> list[Letter]: ...

    @abstractmethod
    def count_all(self) -> int: ...

    @abstractmethod
    def save(self, letter: Letter) -> Letter: ...

    @abstractmethod
    def delete(self, id: UUID) -> None: ...

    @abstractmethod
    def next_sequence_for_year(self, year: int) -> int: ...
