from __future__ import annotations

from enum import Enum


class LetterType(Enum):
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"
    INTERNAL = "INTERNAL"


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


class LetterPriority(Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"
    CRITICAL = "CRITICAL"


class LetterClassification(Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"
    TOP_SECRET = "TOP_SECRET"


class ArchiveStatus(Enum):
    ACTIVE = "ACTIVE"
    SOFT_DELETED = "SOFT_DELETED"
    ARCHIVED = "ARCHIVED"
    PENDING_PURGE = "PENDING_PURGE"
    PURGED = "PURGED"


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
