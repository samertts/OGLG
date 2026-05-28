from __future__ import annotations

from datetime import datetime, timedelta


from app.domain.letters.incoming_letter import IncomingLetter
from app.domain.letters.letter_status import LetterStatus
from app.domain.letters.letter_priority import LetterPriority
from app.domain.letters.letter_classification import LetterClassification
from app.domain.letters.archive_state import ArchiveState


class TestIncomingLetterCreate:
    def test_create_defaults(self) -> None:
        letter = IncomingLetter.create(
            subject="Incoming Request",
            body="Please process the attached documents",
            sender_id="ext-user-1",
            sender_name="External Org",
            sender_department="Ministry of Education",
            department_id="dept-1",
            created_by_id="user-1",
        )
        assert letter.letter_type == "INCOMING"
        assert letter.status == LetterStatus.DRAFT
        assert letter.archive_state == ArchiveState.ACTIVE
        assert letter.version == 1
        assert len(letter._events) == 1
        assert letter.received_date is not None
        assert letter.incoming_number is None
        assert letter.assigned_to is None

    def test_create_with_received_date(self) -> None:
        recv_date = datetime(2026, 5, 15, 10, 30)
        letter = IncomingLetter.create(
            subject="Urgent Request",
            body="Body",
            sender_id="s1",
            sender_name="Sender Co",
            sender_department="Finance",
            department_id="dept-2",
            created_by_id="u1",
            received_date=recv_date,
            incoming_number="EXT-2026-001",
            assigned_to="user-2",
            response_deadline=recv_date + timedelta(days=30),
        )
        assert letter.received_date == recv_date
        assert letter.incoming_number == "EXT-2026-001"
        assert letter.assigned_to == "user-2"
        assert letter.response_deadline == recv_date + timedelta(days=30)

    def test_create_with_priority(self) -> None:
        letter = IncomingLetter.create(
            subject="High Priority",
            body="Body",
            sender_id="s1",
            sender_name="S",
            sender_department="D",
            department_id="d1",
            created_by_id="u1",
            priority=LetterPriority.URGENT,
            classification=LetterClassification.CONFIDENTIAL,
        )
        assert letter.priority == LetterPriority.URGENT
        assert letter.classification == LetterClassification.CONFIDENTIAL


class TestIncomingLetterBehavior:
    def test_assign_to(self) -> None:
        letter = IncomingLetter.create(
            subject="Assign Test",
            body="Body",
            sender_id="s1",
            sender_name="S",
            sender_department="D",
            department_id="d1",
            created_by_id="u1",
        )
        letter.assign_to("user-3")
        assert letter.assigned_to == "user-3"
        assert letter.updated_by_id == "user-3"

    def test_is_overdue_with_deadline(self) -> None:
        letter = IncomingLetter.create(
            subject="Overdue Test",
            body="Body",
            sender_id="s1",
            sender_name="S",
            sender_department="D",
            department_id="d1",
            created_by_id="u1",
            response_deadline=datetime.now() - timedelta(days=1),
        )
        assert letter.is_overdue

    def test_not_overdue_before_deadline(self) -> None:
        letter = IncomingLetter.create(
            subject="Not Overdue",
            body="Body",
            sender_id="s1",
            sender_name="S",
            sender_department="D",
            department_id="d1",
            created_by_id="u1",
            response_deadline=datetime.now() + timedelta(days=30),
        )
        assert not letter.is_overdue

    def test_not_overdue_when_no_deadline(self) -> None:
        letter = IncomingLetter.create(
            subject="No Deadline",
            body="Body",
            sender_id="s1",
            sender_name="S",
            sender_department="D",
            department_id="d1",
            created_by_id="u1",
        )
        assert not letter.is_overdue

    def test_full_lifecycle(self) -> None:
        letter = IncomingLetter.create(
            subject="Full Lifecycle Incoming",
            body="Body",
            sender_id="s1",
            sender_name="Sender",
            sender_department="Dept",
            department_id="d1",
            created_by_id="u1",
        )
        letter.assign_to("reviewer-1")
        assert letter.assigned_to == "reviewer-1"

        letter.submit_for_review("u1")
        assert letter.status == LetterStatus.PENDING_REVIEW

        letter.start_review("reviewer-1")
        assert letter.status == LetterStatus.IN_REVIEW

        letter.approve("reviewer-1", "reviewer-1")
        assert letter.status == LetterStatus.APPROVED

        letter.archive("u1", "Processed")
        assert letter.status == LetterStatus.ARCHIVED

        letter.restore("u1", "Re-open")
        assert letter.status == LetterStatus.RESTORED
