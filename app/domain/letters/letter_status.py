from __future__ import annotations

from enum import Enum


class LetterStatus(Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    RECEIVED = "RECEIVED"
    ARCHIVED = "ARCHIVED"
    RESTORED = "RESTORED"
    DELETED = "DELETED"

    @property
    def is_terminal(self) -> bool:
        return self in (LetterStatus.DELETED,)

    @property
    def is_editable(self) -> bool:
        return self in (LetterStatus.DRAFT, LetterStatus.RESTORED)

    @property
    def is_reviewable(self) -> bool:
        return self in (LetterStatus.PENDING_REVIEW, LetterStatus.IN_REVIEW)
