from __future__ import annotations

from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from app.core.entities.department import Department


class DepartmentRepository(Protocol):
    """Repository interface for Department aggregate."""

    @abstractmethod
    def find_by_id(self, id: UUID) -> Department | None:
        ...

    @abstractmethod
    def find_by_code(self, code: str) -> Department | None:
        ...

    @abstractmethod
    def find_all(self) -> list[Department]:
        ...

    @abstractmethod
    def find_root_departments(self) -> list[Department]:
        ...

    @abstractmethod
    def find_children(self, parent_id: UUID) -> list[Department]:
        ...

    @abstractmethod
    def save(self, department: Department) -> Department:
        ...

    @abstractmethod
    def delete(self, id: UUID) -> None:
        ...
