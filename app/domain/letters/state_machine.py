from __future__ import annotations

from app.domain.letters.archive_state import ArchiveState
from app.domain.letters.letter_status import LetterStatus


class StateTransitionError(Exception):
    def __init__(self, from_status: str, to_status: str, reason: str = "") -> None:
        self.from_status = from_status
        self.to_status = to_status
        self.reason = reason
        super().__init__(f"Cannot transition from {from_status} to {to_status}" + (f": {reason}" if reason else ""))


_ALLOWED_LIFECYCLE: dict[LetterStatus, set[LetterStatus]] = {
    LetterStatus.DRAFT: {LetterStatus.PENDING_REVIEW, LetterStatus.DELETED},
    LetterStatus.PENDING_REVIEW: {LetterStatus.IN_REVIEW, LetterStatus.DRAFT, LetterStatus.DELETED},
    LetterStatus.IN_REVIEW: {LetterStatus.APPROVED, LetterStatus.REJECTED, LetterStatus.DRAFT},
    LetterStatus.APPROVED: {LetterStatus.SENT, LetterStatus.ARCHIVED, LetterStatus.DRAFT},
    LetterStatus.REJECTED: {LetterStatus.DRAFT, LetterStatus.DELETED},
    LetterStatus.SENT: {LetterStatus.DELIVERED, LetterStatus.ARCHIVED, LetterStatus.RESTORED},
    LetterStatus.DELIVERED: {LetterStatus.ARCHIVED, LetterStatus.RESTORED},
    LetterStatus.RECEIVED: {LetterStatus.ARCHIVED, LetterStatus.RESTORED, LetterStatus.PENDING_REVIEW},
    LetterStatus.ARCHIVED: {LetterStatus.RESTORED, LetterStatus.DELETED},
    LetterStatus.RESTORED: {LetterStatus.DRAFT, LetterStatus.ARCHIVED},
    LetterStatus.DELETED: set(),
}

_ALLOWED_ARCHIVE: dict[ArchiveState, set[ArchiveState]] = {
    ArchiveState.ACTIVE: {ArchiveState.SOFT_DELETED, ArchiveState.ARCHIVED},
    ArchiveState.SOFT_DELETED: {ArchiveState.ACTIVE, ArchiveState.ARCHIVED, ArchiveState.PENDING_PURGE},
    ArchiveState.ARCHIVED: {ArchiveState.ACTIVE, ArchiveState.SOFT_DELETED, ArchiveState.PENDING_PURGE},
    ArchiveState.PENDING_PURGE: {ArchiveState.ACTIVE, ArchiveState.PURGED},
    ArchiveState.PURGED: set(),
}


def validate_lifecycle_transition(current: LetterStatus, target: LetterStatus) -> None:
    allowed = _ALLOWED_LIFECYCLE.get(current)
    if allowed is None or target not in allowed:
        raise StateTransitionError(current.value, target.value)


def validate_archive_transition(current: ArchiveState, target: ArchiveState) -> None:
    allowed = _ALLOWED_ARCHIVE.get(current)
    if allowed is None or target not in allowed:
        raise StateTransitionError(current.value, target.value)


def is_terminal(status: LetterStatus) -> bool:
    return status in (LetterStatus.DELETED,)


def is_editable(status: LetterStatus) -> bool:
    return status in (LetterStatus.DRAFT, LetterStatus.RESTORED)


def is_archivable(status: LetterStatus) -> bool:
    return status in (LetterStatus.APPROVED, LetterStatus.SENT, LetterStatus.DELIVERED, LetterStatus.RECEIVED, LetterStatus.RESTORED)


def is_reviewable(status: LetterStatus) -> bool:
    return status in (LetterStatus.PENDING_REVIEW, LetterStatus.IN_REVIEW)
