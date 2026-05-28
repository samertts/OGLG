from __future__ import annotations

from app.domain.letters.enums import (
    ArchiveStatus,
    AttachmentType,
    DeliveryMethod,
    LetterClassification,
    LetterPriority,
    LetterStatus,
    LetterType,
    ReviewAction,
)


class TestLetterType:
    def test_values(self) -> None:
        assert LetterType.INCOMING.value == "INCOMING"
        assert LetterType.OUTGOING.value == "OUTGOING"
        assert LetterType.INTERNAL.value == "INTERNAL"

    def test_all_defined(self) -> None:
        assert len(LetterType) == 3


class TestLetterStatus:
    def test_values(self) -> None:
        assert LetterStatus.DRAFT.value == "DRAFT"
        assert LetterStatus.PENDING_REVIEW.value == "PENDING_REVIEW"
        assert LetterStatus.APPROVED.value == "APPROVED"
        assert LetterStatus.REJECTED.value == "REJECTED"
        assert LetterStatus.SENT.value == "SENT"
        assert LetterStatus.ARCHIVED.value == "ARCHIVED"
        assert LetterStatus.DELETED.value == "DELETED"

    def test_lifecycle_count(self) -> None:
        assert len(LetterStatus) == 11


class TestLetterPriority:
    def test_values(self) -> None:
        assert LetterPriority.NORMAL.value == "NORMAL"
        assert LetterPriority.HIGH.value == "HIGH"
        assert LetterPriority.URGENT.value == "URGENT"
        assert LetterPriority.CRITICAL.value == "CRITICAL"

    def test_order(self) -> None:
        priorities = list(LetterPriority)
        assert priorities[0].value == "LOW"
        assert priorities[-1].value == "CRITICAL"


class TestLetterClassification:
    def test_values(self) -> None:
        assert LetterClassification.PUBLIC.value == "PUBLIC"
        assert LetterClassification.CONFIDENTIAL.value == "CONFIDENTIAL"
        assert LetterClassification.SECRET.value == "SECRET"

    def test_levels(self) -> None:
        assert len(LetterClassification) == 5


class TestArchiveStatus:
    def test_values(self) -> None:
        assert ArchiveStatus.ACTIVE.value == "ACTIVE"
        assert ArchiveStatus.SOFT_DELETED.value == "SOFT_DELETED"
        assert ArchiveStatus.ARCHIVED.value == "ARCHIVED"
        assert ArchiveStatus.PURGED.value == "PURGED"


class TestReviewAction:
    def test_values(self) -> None:
        assert ReviewAction.APPROVE.value == "APPROVE"
        assert ReviewAction.REJECT.value == "REJECT"


class TestAttachmentType:
    def test_values(self) -> None:
        assert AttachmentType.PDF.value == "PDF"
        assert AttachmentType.IMAGE.value == "IMAGE"


class TestDeliveryMethod:
    def test_values(self) -> None:
        assert DeliveryMethod.COURIER.value == "COURIER"
        assert DeliveryMethod.EMAIL.value == "EMAIL"
        assert DeliveryMethod.FAX.value == "FAX"
