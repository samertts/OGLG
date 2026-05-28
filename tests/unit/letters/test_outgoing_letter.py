from __future__ import annotations



from app.domain.letters.outgoing_letter import OutgoingLetter
from app.domain.letters.letter_status import LetterStatus
from app.domain.letters.letter_priority import LetterPriority
from app.domain.letters.letter_classification import LetterClassification
from app.domain.letters.archive_state import ArchiveState
from app.domain.letters.delivery_status import DeliveryStatus, DeliveryMethod
from app.domain.letters.delivery_metadata import DeliveryMetadata


class TestOutgoingLetterCreate:
    def test_create_defaults(self) -> None:
        letter = OutgoingLetter.create(
            subject="Official Letter",
            body="This is an official communication",
            sender_id="user-1",
            sender_name="Director",
            sender_department="MOH",
            department_id="dept-1",
            created_by_id="user-1",
            recipient_name="Ministry of Finance",
            recipient_department="Procurement",
        )
        assert letter.letter_type == "OUTGOING"
        assert letter.status == LetterStatus.DRAFT
        assert letter.archive_state == ArchiveState.ACTIVE
        assert letter.version == 1
        assert len(letter._events) == 1
        assert letter.recipient_name == "Ministry of Finance"
        assert letter.delivery_status == DeliveryStatus.PENDING

    def test_create_with_delivery(self) -> None:
        delivery = DeliveryMetadata.create(
            method=DeliveryMethod.COURIER,
            recipient_name="MoF",
            recipient_department="Procurement",
            recipient_address="Baghdad",
        )
        letter = OutgoingLetter.create(
            subject="With Delivery",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="d1",
            created_by_id="u1",
            recipient_name="MoF",
            recipient_department="Procurement",
            delivery=delivery,
        )
        assert letter.delivery is not None
        assert letter.delivery.method == DeliveryMethod.COURIER

    def test_create_with_priority(self) -> None:
        letter = OutgoingLetter.create(
            subject="Critical",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="d1",
            created_by_id="u1",
            recipient_name="MoF",
            recipient_department="Procurement",
            priority=LetterPriority.CRITICAL,
            classification=LetterClassification.SECRET,
        )
        assert letter.priority == LetterPriority.CRITICAL
        assert letter.classification == LetterClassification.SECRET


class TestOutgoingLetterBehavior:
    def test_mark_sent(self) -> None:
        letter = OutgoingLetter.create(
            subject="Send Test",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="d1",
            created_by_id="u1",
            recipient_name="Recipient",
            recipient_department="Dept",
        )
        letter.submit_for_review("u1")
        letter.start_review("u2")
        letter.approve("u2", "u2")
        letter.mark_sent("u1", tracking_number="TRACK-001")
        assert letter.status == LetterStatus.SENT
        assert letter.sent_date is not None
        assert letter.delivery_status == DeliveryStatus.IN_TRANSIT
        assert letter.tracking_number == "TRACK-001"

    def test_mark_delivered(self) -> None:
        letter = OutgoingLetter.create(
            subject="Deliver Test",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="d1",
            created_by_id="u1",
            recipient_name="Recipient",
            recipient_department="Dept",
        )
        letter.submit_for_review("u1")
        letter.start_review("u2")
        letter.approve("u2", "u2")
        letter.mark_sent("u1")
        letter.mark_delivered("u2", proof="signed_receipt.pdf")
        assert letter.status == LetterStatus.DELIVERED
        assert letter.delivery_status == DeliveryStatus.DELIVERED
        assert letter.proof_of_delivery == "signed_receipt.pdf"

    def test_has_tracking(self) -> None:
        letter = OutgoingLetter.create(
            subject="Track Test",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="d1",
            created_by_id="u1",
            recipient_name="Recipient",
            recipient_department="Dept",
        )
        assert not letter.has_tracking
        letter.submit_for_review("u1")
        letter.start_review("u2")
        letter.approve("u2", "u2")
        letter.mark_sent("u1", tracking_number="TRK-001")
        assert letter.has_tracking

    def test_is_in_transit(self) -> None:
        letter = OutgoingLetter.create(
            subject="Transit Test",
            body="Body",
            sender_id="u1",
            sender_name="U1",
            sender_department="D1",
            department_id="d1",
            created_by_id="u1",
            recipient_name="Recipient",
            recipient_department="Dept",
        )
        assert not letter.is_in_transit
        letter.submit_for_review("u1")
        letter.start_review("u2")
        letter.approve("u2", "u2")
        letter.mark_sent("u1")
        assert letter.is_in_transit

    def test_full_lifecycle(self) -> None:
        letter = OutgoingLetter.create(
            subject="Full Lifecycle Outgoing",
            body="Body",
            sender_id="u1",
            sender_name="Sender",
            sender_department="Dept",
            department_id="d1",
            created_by_id="u1",
            recipient_name="Recipient",
            recipient_department="Dept",
        )
        letter.submit_for_review("u1")
        assert letter.status == LetterStatus.PENDING_REVIEW

        letter.start_review("u2")
        letter.approve("u2", "u2", "Approved")
        assert letter.status == LetterStatus.APPROVED

        letter.assign_number("MOH-2026-000001", "u1")
        assert letter.number == "MOH-2026-000001"

        letter.mark_sent("u1", tracking_number="POST-001")
        assert letter.status == LetterStatus.SENT

        letter.mark_delivered("u2", proof="pod.pdf")
        assert letter.status == LetterStatus.DELIVERED

        letter.archive("u1", "Completed")
        assert letter.status == LetterStatus.ARCHIVED

        letter.restore("u1", "Amendment needed")
        assert letter.status == LetterStatus.RESTORED
