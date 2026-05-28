from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Base repository interface following the repository pattern."""

    @abstractmethod
    def find_by_id(self, id: UUID) -> T | None: ...

    @abstractmethod
    def save(self, entity: T) -> T: ...

    @abstractmethod
    def delete(self, id: UUID) -> None: ...


class ReadOnlyRepository(ABC, Generic[T]):
    """Base interface for append-only repositories (audit, archive, backup)."""

    @abstractmethod
    def find_by_id(self, id: UUID) -> T | None: ...


class AppendOnlyRepository(ABC, Generic[T]):
    """Base interface for append-only repositories."""

    @abstractmethod
    def append(self, entry: T) -> T: ...

    @abstractmethod
    def find_by_id(self, id: UUID) -> T | None: ...
