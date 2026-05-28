from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Department:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    code: str = ""
    parent_id: UUID | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
