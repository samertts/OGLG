from __future__ import annotations

from datetime import datetime, timedelta


from app.domain.letters.internal_letter import InternalLetter
from app.domain.letters.letter_status import LetterStatus
from app.domain.letters.letter_priority import LetterPriority
from app.domain.letters.archive_state import ArchiveState
from app.domain.letters.correspondence_party import CorrespondenceParty


class TestInternalLetterCreate:
    def test_create_defaults(self) -> None:
        letter = InternalLetter.create(
            subject="Internal Memo",
            body="Please review the attached proposal",
            sender_id="user-1",
            sender_name="Manager",
            sender_department="HR",
            department_id="dept-1",
            created_by_id="user-1",
        )
        assert letter.letter_type == "INTERNAL"
        assert letter.status == LetterStatus.DRAFT
        assert letter.archive_state == ArchiveState.ACTIVE
        assert letter.version == 1
        assert len(letter._events) == 1
        assert letter.from_department == "HR"
        assert not letter.requires_acknowledgment

    def test_create_with_departments(self) -> None:
        letter = InternalLetter.create(
            subject="Cross-Dept Memo",
            body="Coordination needed",
            sender_id="u1",
            sender_name="U1",
            sender_department="HR",
            department_id="dept-1",
            created_by_id="u1",
            from_department="HR",
            to_department="IT",
            requires_acknowledgment=True,
        )
        assert letter.from_department == "HR"
        assert letter.to_department == "IT"
        assert letter.requires_acknowledgment
        assert not letter.acknowledgment_received

    def test_create_with_deadline(self) -> None:
        deadline = datetime.now() + timedelta(days=7)
        letter = InternalLetter.create(
            subject="Time-Sensitive",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="Dept",
            department_id="d1",
            created_by_id="u1",
            internal_deadline=deadline,
            priority=LetterPriority.HIGH,
        )
        assert letter.internal_deadline == deadline
        assert letter.priority == LetterPriority.HIGH


class TestInternalLetterBehavior:
    def test_add_to_circulation(self) -> None:
        letter = InternalLetter.create(
            subject="Circulation Test",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="Dept",
            department_id="d1",
            created_by_id="u1",
        )
        party = CorrespondenceParty(
            id="p1", name="Reviewer A", department="Legal", title="Lawyer"
        )
        letter.add_to_circulation(party)
        assert letter.circulation_count == 1

    def test_add_duplicate_circulation(self) -> None:
        letter = InternalLetter.create(
            subject="Dup Test",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="Dept",
            department_id="d1",
            created_by_id="u1",
        )
        party = CorrespondenceParty(
            id="p1", name="Reviewer A", department="Legal"
        )
        letter.add_to_circulation(party)
        letter.add_to_circulation(party)
        assert letter.circulation_count == 1

    def test_remove_from_circulation(self) -> None:
        letter = InternalLetter.create(
            subject="Remove Test",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="Dept",
            department_id="d1",
            created_by_id="u1",
        )
        party = CorrespondenceParty(
            id="p1", name="Reviewer A", department="Legal"
        )
        letter.add_to_circulation(party)
        letter.remove_from_circulation("p1")
        assert letter.circulation_count == 0

    def test_acknowledge(self) -> None:
        letter = InternalLetter.create(
            subject="Ack Test",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="Dept",
            department_id="d1",
            created_by_id="u1",
            requires_acknowledgment=True,
        )
        assert letter.is_acknowledgment_pending
        letter.acknowledge("u2")
        assert letter.acknowledgment_received
        assert not letter.is_acknowledgment_pending

    def test_is_acknowledgment_pending_no_ack_required(self) -> None:
        letter = InternalLetter.create(
            subject="No Ack Needed",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="Dept",
            department_id="d1",
            created_by_id="u1",
        )
        assert not letter.is_acknowledgment_pending

    def test_full_lifecycle(self) -> None:
        letter = InternalLetter.create(
            subject="Full Lifecycle Internal",
            body="Body",
            sender_id="u1",
            sender_name="Sender",
            sender_department="HR",
            department_id="d1",
            created_by_id="u1",
            to_department="IT",
            requires_acknowledgment=True,
        )
        party = CorrespondenceParty(
            id="p1", name="IT Head", department="IT"
        )
        letter.add_to_circulation(party)
        assert letter.circulation_count == 1

        letter.submit_for_review("u1")
        assert letter.status == LetterStatus.PENDING_REVIEW

        letter.start_review("u2")
        letter.approve("u2", "u2", "Reviewed")
        assert letter.status == LetterStatus.APPROVED

        letter.acknowledge("u2")
        assert letter.acknowledgment_received

        letter.archive("u1", "Completed")
        assert letter.status == LetterStatus.ARCHIVED
