from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.core.enums import UserRole


@dataclass
class User:
    id: UUID = field(default_factory=uuid4)
    username: str = ""
    full_name: str = ""
    title: str = ""
    email: str | None = None
    password_hash: str = ""
    role: UserRole = UserRole.VIEWER
    department_id: UUID | None = None
    is_active: bool = True
    last_login_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now()

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now()

    def record_login(self) -> None:
        self.last_login_at = datetime.now()
