from __future__ import annotations

from abc import abstractmethod
from typing import Protocol
from uuid import UUID

from app.core.entities.user import User
from app.core.enums import UserRole


class UserRepository(Protocol):
    """Repository interface for User aggregate."""

    @abstractmethod
    def find_by_id(self, id: UUID) -> User | None: ...

    @abstractmethod
    def find_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    def find_all(self, offset: int = 0, limit: int = 50) -> list[User]: ...

    @abstractmethod
    def find_by_department(self, department_id: UUID) -> list[User]: ...

    @abstractmethod
    def find_by_role(self, role: UserRole) -> list[User]: ...

    @abstractmethod
    def count_all(self) -> int: ...

    @abstractmethod
    def save(self, user: User) -> User: ...

    @abstractmethod
    def update_last_login(self, user_id: UUID) -> None: ...
