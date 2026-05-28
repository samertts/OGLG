from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any


class EventType(Enum):
    LETTER_CREATED = auto()
    LETTER_EDITED = auto()
    LETTER_SUBMITTED_FOR_REVIEW = auto()
    LETTER_REVIEW_STARTED = auto()
    LETTER_APPROVED = auto()
    LETTER_REJECTED = auto()
    LETTER_SENT = auto()
    LETTER_DELIVERED = auto()
    LETTER_RECEIVED = auto()
    LETTER_ARCHIVED = auto()
    LETTER_RESTORED = auto()
    LETTER_SOFT_DELETED = auto()
    LETTER_PRINTED = auto()
    LETTER_EXPORTED = auto()
    LETTER_NUMBER_ASSIGNED = auto()
    ATTACHMENT_ADDED = auto()
    ATTACHMENT_REMOVED = auto()
    LETTER_ROUTED = auto()
    LETTER_FORWARDED = auto()


@dataclass(frozen=True)
class DomainEvent:
    event_id: str
    event_type: EventType
    aggregate_id: str
    timestamp: datetime
    user_id: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LetterCreated(DomainEvent):
    @staticmethod
    def create(letter_id: str, user_id: str, data: dict[str, Any]) -> LetterCreated:
        import uuid

        return LetterCreated(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LETTER_CREATED,
            aggregate_id=letter_id,
            timestamp=datetime.now(),
            user_id=user_id,
            data=data,
        )


@dataclass(frozen=True)
class LetterEdited(DomainEvent):
    @staticmethod
    def create(letter_id: str, user_id: str, changes: dict[str, Any]) -> LetterEdited:
        import uuid

        return LetterEdited(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LETTER_EDITED,
            aggregate_id=letter_id,
            timestamp=datetime.now(),
            user_id=user_id,
            data={"changes": changes},
        )


@dataclass(frozen=True)
class LetterSubmitted(DomainEvent):
    @staticmethod
    def create(letter_id: str, user_id: str) -> LetterSubmitted:
        import uuid

        return LetterSubmitted(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LETTER_SUBMITTED_FOR_REVIEW,
            aggregate_id=letter_id,
            timestamp=datetime.now(),
            user_id=user_id,
        )


@dataclass(frozen=True)
class LetterApproved(DomainEvent):
    @staticmethod
    def create(letter_id: str, user_id: str, reviewer_id: str, notes: str = "") -> LetterApproved:
        import uuid

        return LetterApproved(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LETTER_APPROVED,
            aggregate_id=letter_id,
            timestamp=datetime.now(),
            user_id=user_id,
            data={"reviewer_id": reviewer_id, "notes": notes},
        )


@dataclass(frozen=True)
class LetterRejected(DomainEvent):
    @staticmethod
    def create(letter_id: str, user_id: str, reviewer_id: str, reason: str) -> LetterRejected:
        import uuid

        return LetterRejected(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LETTER_REJECTED,
            aggregate_id=letter_id,
            timestamp=datetime.now(),
            user_id=user_id,
            data={"reviewer_id": reviewer_id, "reason": reason},
        )


@dataclass(frozen=True)
class LetterArchived(DomainEvent):
    @staticmethod
    def create(letter_id: str, user_id: str, reason: str = "") -> LetterArchived:
        import uuid

        return LetterArchived(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LETTER_ARCHIVED,
            aggregate_id=letter_id,
            timestamp=datetime.now(),
            user_id=user_id,
            data={"reason": reason},
        )


@dataclass(frozen=True)
class LetterRestored(DomainEvent):
    @staticmethod
    def create(letter_id: str, user_id: str, reason: str = "") -> LetterRestored:
        import uuid

        return LetterRestored(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LETTER_RESTORED,
            aggregate_id=letter_id,
            timestamp=datetime.now(),
            user_id=user_id,
            data={"reason": reason},
        )


@dataclass(frozen=True)
class LetterDeleted(DomainEvent):
    @staticmethod
    def create(letter_id: str, user_id: str, reason: str = "") -> LetterDeleted:
        import uuid

        return LetterDeleted(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LETTER_SOFT_DELETED,
            aggregate_id=letter_id,
            timestamp=datetime.now(),
            user_id=user_id,
            data={"reason": reason},
        )


@dataclass(frozen=True)
class LetterPrinted(DomainEvent):
    @staticmethod
    def create(letter_id: str, user_id: str, copies: int = 1) -> LetterPrinted:
        import uuid

        return LetterPrinted(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LETTER_PRINTED,
            aggregate_id=letter_id,
            timestamp=datetime.now(),
            user_id=user_id,
            data={"copies": copies},
        )


@dataclass(frozen=True)
class LetterNumberAssigned(DomainEvent):
    @staticmethod
    def create(letter_id: str, user_id: str, number: str) -> LetterNumberAssigned:
        import uuid

        return LetterNumberAssigned(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LETTER_NUMBER_ASSIGNED,
            aggregate_id=letter_id,
            timestamp=datetime.now(),
            user_id=user_id,
            data={"number": number},
        )
