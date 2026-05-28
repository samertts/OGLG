from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class AuditEntry:
    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: UUID | None = None
    action: str = ""
    entity_type: str = ""
    entity_id: str = ""
    details_json: str = "{}"
    ip_address: str | None = None
    result: str = "success"
