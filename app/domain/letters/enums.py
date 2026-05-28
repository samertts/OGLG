"""Backward-compatible re-exports for the refactored domain layer.

Enums have been moved to individual files:
  - letter_status.py: LetterStatus
  - letter_priority.py: LetterPriority
  - letter_classification.py: LetterClassification
  - delivery_status.py: DeliveryMethod, DeliveryStatus
  - archive_state.py: ArchiveState (was ArchiveStatus)
  - review_assignment.py: ReviewAction
  - attachment.py: AttachmentType
"""

from enum import Enum

from app.domain.letters.archive_state import ArchiveState as ArchiveStatus
from app.domain.letters.letter import LetterType
from app.domain.letters.letter_classification import LetterClassification
from app.domain.letters.letter_priority import LetterPriority
from app.domain.letters.letter_status import LetterStatus


class ReviewAction(Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    RETURN_TO_DRAFT = "RETURN_TO_DRAFT"


class DeliveryMethod(Enum):
    COURIER = "COURIER"
    POSTAL = "POSTAL"
    FAX = "FAX"
    EMAIL = "EMAIL"
    INTERNAL = "INTERNAL"
    HAND_DELIVERY = "HAND_DELIVERY"


class AttachmentType(Enum):
    PDF = "PDF"
    IMAGE = "IMAGE"
    DOCUMENT = "DOCUMENT"
    SPREADSHEET = "SPREADSHEET"
    ARCHIVE = "ARCHIVE"
    OTHER = "OTHER"


__all__ = [
    "ArchiveStatus",
    "AttachmentType",
    "DeliveryMethod",
    "LetterClassification",
    "LetterPriority",
    "LetterStatus",
    "LetterType",
    "ReviewAction",
]
