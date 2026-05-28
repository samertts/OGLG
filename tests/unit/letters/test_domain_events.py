from __future__ import annotations

from app.domain.letters.events import (
    EventType,
    LetterApproved,
    LetterArchived,
    LetterCreated,
    LetterDeleted,
    LetterEdited,
    LetterNumberAssigned,
    LetterPrinted,
    LetterRejected,
    LetterRestored,
    LetterSubmitted,
)


class TestDomainEvents:
    def test_letter_created(self) -> None:
        event = LetterCreated.create(
            "letter-1", "user-1", {"letter_type": "OUTGOING", "subject": "Test"}
        )
        assert event.event_type == EventType.LETTER_CREATED
        assert event.aggregate_id == "letter-1"
        assert event.user_id == "user-1"
        assert event.data["letter_type"] == "OUTGOING"

    def test_letter_edited(self) -> None:
        event = LetterEdited.create("letter-1", "user-1", {"subject": {"old": "A", "new": "B"}})
        assert event.event_type == EventType.LETTER_EDITED
        assert "subject" in event.data["changes"]

    def test_letter_submitted(self) -> None:
        event = LetterSubmitted.create("letter-1", "user-1")
        assert event.event_type == EventType.LETTER_SUBMITTED_FOR_REVIEW

    def test_letter_approved(self) -> None:
        event = LetterApproved.create("letter-1", "user-1", "reviewer-1", "Looks good")
        assert event.event_type == EventType.LETTER_APPROVED
        assert event.data["reviewer_id"] == "reviewer-1"
        assert event.data["notes"] == "Looks good"

    def test_letter_rejected(self) -> None:
        event = LetterRejected.create("letter-1", "user-1", "reviewer-1", "Missing info")
        assert event.event_type == EventType.LETTER_REJECTED
        assert event.data["reason"] == "Missing info"

    def test_letter_archived(self) -> None:
        event = LetterArchived.create("letter-1", "user-1", "Retention policy")
        assert event.event_type == EventType.LETTER_ARCHIVED

    def test_letter_restored(self) -> None:
        event = LetterRestored.create("letter-1", "user-1", "User request")
        assert event.event_type == EventType.LETTER_RESTORED

    def test_letter_deleted(self) -> None:
        event = LetterDeleted.create("letter-1", "user-1", "No longer needed")
        assert event.event_type == EventType.LETTER_SOFT_DELETED

    def test_letter_printed(self) -> None:
        event = LetterPrinted.create("letter-1", "user-1", copies=3)
        assert event.event_type == EventType.LETTER_PRINTED
        assert event.data["copies"] == 3

    def test_letter_number_assigned(self) -> None:
        event = LetterNumberAssigned.create("letter-1", "user-1", "MOH-2026-000001")
        assert event.event_type == EventType.LETTER_NUMBER_ASSIGNED
        assert event.data["number"] == "MOH-2026-000001"

    def test_events_have_unique_ids(self) -> None:
        e1 = LetterCreated.create("l1", "u1", {})
        e2 = LetterCreated.create("l1", "u1", {})
        assert e1.event_id != e2.event_id

    def test_events_are_frozen(self) -> None:
        event = LetterCreated.create("l1", "u1", {})
        import pytest
        with pytest.raises(AttributeError):
            event.user_id = "other"
