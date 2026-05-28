from __future__ import annotations

from datetime import datetime

import pytest

from app.domain.letters.letter import Letter
from app.domain.letters.letter_status import LetterStatus
from app.domain.letters.letter_priority import LetterPriority
from app.domain.letters.letter_classification import LetterClassification
from app.domain.letters.letter import LetterType
from app.domain.letters.archive_state import ArchiveState
from app.domain.letters.events import EventType
from app.domain.letters.attachment import Attachment


class TestLetterCreate:
    def test_create_draft(self) -> None:
        letter = Letter.create(
            letter_type=LetterType.OUTGOING.value,
            subject="Test Subject",
            body="Test body content",
            sender_id="user-1",
            sender_name="Ali Ahmed",
            sender_department="MOH",
            department_id="dept-1",
            created_by_id="user-1",
        )
        assert letter.status == LetterStatus.DRAFT
        assert letter.archive_state == ArchiveState.ACTIVE
        assert letter.subject == "Test Subject"
        assert letter.version == 1
        assert len(letter._events) == 1
        assert letter._events[0].event_type == EventType.LETTER_CREATED

    def test_create_with_full_params(self) -> None:
        letter = Letter.create(
            letter_type=LetterType.INCOMING.value,
            subject="Incoming Letter",
            body="Body",
            sender_id="user-2",
            sender_name="Sara Ali",
            sender_department="MOE",
            department_id="dept-2",
            created_by_id="user-2",
            priority=LetterPriority.HIGH,
            classification=LetterClassification.CONFIDENTIAL,
            language="AR",
            recipient_name="Minister",
            recipient_department="Cabinet",
        )
        assert letter.letter_type == LetterType.INCOMING.value
        assert letter.priority == LetterPriority.HIGH
        assert letter.classification == LetterClassification.CONFIDENTIAL

    def test_create_outgoing(self) -> None:
        letter = Letter.create(
            letter_type=LetterType.OUTGOING.value,
            subject="Outgoing",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="D1",
            created_by_id="u1",
        )
        assert letter.letter_type == LetterType.OUTGOING.value

    def test_create_internal(self) -> None:
        letter = Letter.create(
            letter_type=LetterType.INTERNAL.value,
            subject="Internal",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="D1",
            created_by_id="u1",
        )
        assert letter.letter_type == LetterType.INTERNAL.value


class TestLetterLifecycle:
    def test_full_lifecycle_outgoing(self) -> None:
        letter = Letter.create(
            letter_type=LetterType.OUTGOING.value,
            subject="Full Lifecycle",
            body="Test",
            sender_id="u1",
            sender_name="User",
            sender_department="Dept",
            department_id="dept-1",
            created_by_id="u1",
        )
        letter.submit_for_review("u1")
        assert letter.status == LetterStatus.PENDING_REVIEW

        letter.start_review("u2")
        assert letter.status == LetterStatus.IN_REVIEW

        letter.approve("u2", "u2", "Approved")
        assert letter.status == LetterStatus.APPROVED

        letter.mark_sent("u1")
        assert letter.status == LetterStatus.SENT

        letter.mark_delivered("u2", proof="proof.pdf")
        assert letter.status == LetterStatus.DELIVERED

        letter.archive("u1", "Retention policy")
        assert letter.status == LetterStatus.ARCHIVED
        assert letter.is_archived is True

        letter.restore("u1", "Requested")
        assert letter.status == LetterStatus.RESTORED
        assert letter.is_archived is False

    def test_reject_and_redraft(self) -> None:
        letter = Letter.create(
            letter_type=LetterType.OUTGOING.value,
            subject="Reject Test",
            body="Body",
            sender_id="u1",
            sender_name="User",
            sender_department="Dept",
            department_id="dept-1",
            created_by_id="u1",
        )
        letter.submit_for_review("u1")
        letter.start_review("u2")
        letter.reject("u2", "u2", "Missing signature")
        assert letter.status == LetterStatus.REJECTED

        letter.return_to_draft("u1")
        assert letter.status == LetterStatus.DRAFT

        letter.edit("u1", body="Updated body with signature")
        assert letter.status == LetterStatus.DRAFT
        letter.submit_for_review("u1")
        assert letter.status == LetterStatus.PENDING_REVIEW

    def test_soft_delete(self) -> None:
        letter = Letter.create(
            letter_type=LetterType.OUTGOING.value,
            subject="Delete Test",
            body="Body",
            sender_id="u1",
            sender_name="User",
            sender_department="Dept",
            department_id="dept-1",
            created_by_id="u1",
        )
        letter.soft_delete("u1", "No longer needed")
        assert letter.status == LetterStatus.DELETED
        assert letter.archive_state == ArchiveState.SOFT_DELETED

    def test_edit_draft(self) -> None:
        letter = Letter.create(
            letter_type=LetterType.OUTGOING.value,
            subject="Original",
            body="Original body",
            sender_id="u1",
            sender_name="User",
            sender_department="Dept",
            department_id="dept-1",
            created_by_id="u1",
        )
        letter.edit("u1", subject="Updated Subject", body="Updated body")
        assert letter.subject == "Updated Subject"
        assert letter.body == "Updated body"
        assert letter.version == 2

    def test_cannot_edit_after_submit(self) -> None:
        letter = Letter.create(
            letter_type=LetterType.OUTGOING.value,
            subject="No Edit",
            body="Body",
            sender_id="u1",
            sender_name="User",
            sender_department="Dept",
            department_id="dept-1",
            created_by_id="u1",
        )
        letter.submit_for_review("u1")
        with pytest.raises(ValueError):
            letter.edit("u1", subject="Trying to edit")

    def test_assign_number(self) -> None:
        letter = Letter.create(
            letter_type=LetterType.OUTGOING.value,
            subject="Number Test",
            body="Body",
            sender_id="u1",
            sender_name="User",
            sender_department="Dept",
            department_id="dept-1",
            created_by_id="u1",
        )
        letter.assign_number("MOH-2026-000001", "u1")
        assert letter.number == "MOH-2026-000001"

    def test_pop_events(self) -> None:
        letter = Letter.create(
            letter_type=LetterType.OUTGOING.value,
            subject="Events",
            body="Body",
            sender_id="u1",
            sender_name="User",
            sender_department="Dept",
            department_id="dept-1",
            created_by_id="u1",
        )
        events = letter.pop_events()
        assert len(events) == 1
        assert len(letter._events) == 0


class TestAttachments:
    def test_add_attachment(self) -> None:
        letter = Letter.create(
            letter_type=LetterType.OUTGOING.value,
            subject="Attachment Test",
            body="Body",
            sender_id="u1",
            sender_name="User",
            sender_department="Dept",
            department_id="dept-1",
            created_by_id="u1",
        )
        att = Attachment(
            id="att-1",
            letter_id=letter.id,
            filename="doc.pdf",
            original_name="doc.pdf",
            mime_type="application/pdf",
            file_size=1024,
            extension=".pdf",
            sha256_hash="abc",
            storage_path="/path/doc.pdf",
            uploaded_at=datetime.now(),
            uploaded_by="u1",
        )
        letter.add_attachment(att)
        assert len(letter.attachments) == 1

    def test_remove_attachment(self) -> None:
        letter = Letter.create(
            letter_type=LetterType.OUTGOING.value,
            subject="Remove Att",
            body="Body",
            sender_id="u1",
            sender_name="User",
            sender_department="Dept",
            department_id="dept-1",
            created_by_id="u1",
        )
        att = Attachment(
            id="att-1",
            letter_id=letter.id,
            filename="doc.pdf",
            original_name="doc.pdf",
            mime_type="application/pdf",
            file_size=1024,
            extension=".pdf",
            sha256_hash="abc",
            storage_path="/path/doc.pdf",
            uploaded_at=datetime.now(),
            uploaded_by="u1",
        )
        letter.add_attachment(att)
        letter.remove_attachment("att-1")
        assert len(letter.attachments) == 0

    def test_record_print(self) -> None:
        letter = Letter.create(
            letter_type=LetterType.OUTGOING.value,
            subject="Print Test",
            body="Body",
            sender_id="u1",
            sender_name="User",
            sender_department="Dept",
            department_id="dept-1",
            created_by_id="u1",
        )
        letter.record_print("u1", copies=2)
        events = letter.pop_events()
        assert any(e.event_type == EventType.LETTER_PRINTED for e in events)
