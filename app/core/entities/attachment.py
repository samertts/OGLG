from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Attachment:
    id: UUID = field(default_factory=uuid4)
    letter_id: UUID | None = None
    filename: str = ""
    original_name: str = ""
    file_path: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    hash_sha256: str = ""
    created_at: datetime = field(default_factory=datetime.now)
