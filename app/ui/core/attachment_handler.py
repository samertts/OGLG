from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any


class AttachmentState(Enum):
    PENDING = auto()
    STORED = auto()
    FAILED = auto()


@dataclass
class AttachmentRef:
    attachment_id: str
    letter_id: str
    filename: str
    mime_type: str = "application/octet-stream"
    size_bytes: int = 0
    state: AttachmentState = AttachmentState.PENDING
    checksum: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


class AttachmentHandler:
    MAX_ATTACHMENTS_PER_LETTER = 10
    MAX_TOTAL_ATTACHMENTS = 500

    def __init__(self) -> None:
        self._attachments: dict[str, list[AttachmentRef]] = {}

    @property
    def total_attachments(self) -> int:
        return sum(len(atts) for atts in self._attachments.values())

    def add_attachment(
        self, letter_id: str, attachment_id: str,
        filename: str, mime_type: str = "application/octet-stream",
        size_bytes: int = 0,
    ) -> AttachmentRef | None:
        if self.total_attachments >= self.MAX_TOTAL_ATTACHMENTS:
            return None
        current = len(self._attachments.get(letter_id, []))
        if current >= self.MAX_ATTACHMENTS_PER_LETTER:
            return None
        ref = AttachmentRef(
            attachment_id=attachment_id,
            letter_id=letter_id,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
        )
        if letter_id not in self._attachments:
            self._attachments[letter_id] = []
        self._attachments[letter_id].append(ref)
        return ref

    def remove_attachment(self, letter_id: str, attachment_id: str) -> bool:
        atts = self._attachments.get(letter_id)
        if atts is None:
            return False
        before = len(atts)
        self._attachments[letter_id] = [a for a in atts if a.attachment_id != attachment_id]
        return len(self._attachments[letter_id]) < before

    def get_attachments(self, letter_id: str) -> list[AttachmentRef]:
        return list(self._attachments.get(letter_id, []))

    def mark_stored(self, attachment_id: str, checksum: str | None = None) -> bool:
        for atts in self._attachments.values():
            for a in atts:
                if a.attachment_id == attachment_id:
                    a.state = AttachmentState.STORED
                    a.checksum = checksum
                    return True
        return False

    def clear(self) -> None:
        self._attachments.clear()
