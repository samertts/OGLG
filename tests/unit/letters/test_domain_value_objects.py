from __future__ import annotations


import pytest

from app.domain.letters.archive_state import ArchiveState
from app.domain.letters.correspondence_party import CorrespondenceParty
from app.domain.letters.delivery_metadata import DeliveryMetadata
from app.domain.letters.delivery_status import DeliveryMethod, DeliveryStatus
from app.domain.letters.signature_metadata import SignatureMetadata
from app.domain.letters.review_assignment import ReviewAssignment
from app.domain.letters.routing_step import RoutingStep


class TestArchiveState:
    def test_values(self) -> None:
        assert ArchiveState.ACTIVE.value == "ACTIVE"
        assert ArchiveState.SOFT_DELETED.value == "SOFT_DELETED"
        assert ArchiveState.ARCHIVED.value == "ARCHIVED"
        assert ArchiveState.PENDING_PURGE.value == "PENDING_PURGE"
        assert ArchiveState.PURGED.value == "PURGED"

    def test_is_recoverable(self) -> None:
        assert ArchiveState.ACTIVE.is_recoverable
        assert ArchiveState.SOFT_DELETED.is_recoverable
        assert ArchiveState.ARCHIVED.is_recoverable
        assert not ArchiveState.PENDING_PURGE.is_recoverable
        assert not ArchiveState.PURGED.is_recoverable

    def test_is_accessible(self) -> None:
        assert ArchiveState.ACTIVE.is_accessible
        assert ArchiveState.ARCHIVED.is_accessible
        assert not ArchiveState.SOFT_DELETED.is_accessible
        assert not ArchiveState.PENDING_PURGE.is_accessible
        assert not ArchiveState.PURGED.is_accessible


class TestCorrespondenceParty:
    def test_create(self) -> None:
        party = CorrespondenceParty(
            id="p1", name="Ali Ahmed", department="MOH", title="Director"
        )
        assert party.id == "p1"
        assert party.display_name == "Director Ali Ahmed"

    def test_display_name_no_title(self) -> None:
        party = CorrespondenceParty(
            id="p2", name="Sara Ali", department="MOE"
        )
        assert party.display_name == "Sara Ali"

    def test_full_department_path(self) -> None:
        party = CorrespondenceParty(
            id="p3", name="User", department="HR", title="Manager"
        )
        assert party.full_department_path == "HR / Manager"

    def test_full_department_path_no_title(self) -> None:
        party = CorrespondenceParty(
            id="p4", name="User", department="IT"
        )
        assert party.full_department_path == "IT"

    def test_immutable(self) -> None:
        party = CorrespondenceParty(
            id="p1", name="Name", department="Dept"
        )
        with pytest.raises(AttributeError):
            party.name = "Changed"


class TestDeliveryMetadata:
    def test_create(self) -> None:
        dm = DeliveryMetadata.create(
            method=DeliveryMethod.COURIER,
            recipient_name="Ministry of Health",
            recipient_department="Procurement",
            recipient_address="Baghdad",
        )
        assert dm.method == DeliveryMethod.COURIER
        assert dm.status == DeliveryStatus.PENDING

    def test_mark_sent(self) -> None:
        dm = DeliveryMetadata.create(
            method=DeliveryMethod.POSTAL,
            recipient_name="Recipient",
            recipient_department="Dept",
            recipient_address="Address",
        )
        dm.mark_sent()
        assert dm.status == DeliveryStatus.IN_TRANSIT
        assert dm.sent_at is not None

    def test_mark_delivered(self) -> None:
        dm = DeliveryMetadata.create(
            method=DeliveryMethod.COURIER,
            recipient_name="Recipient",
            recipient_department="Dept",
            recipient_address="Address",
        )
        dm.mark_sent()
        dm.mark_delivered("user-1", proof="proof.pdf")
        assert dm.status == DeliveryStatus.DELIVERED
        assert dm.delivered_at is not None
        assert dm.confirmed_by == "user-1"
        assert dm.proof_of_delivery == "proof.pdf"

    def test_mark_confirmed(self) -> None:
        dm = DeliveryMetadata.create(
            method=DeliveryMethod.EMAIL,
            recipient_name="Recipient",
            recipient_department="Dept",
            recipient_address="Address",
        )
        dm.mark_sent()
        dm.mark_delivered("user-1")
        dm.mark_confirmed()
        assert dm.status == DeliveryStatus.CONFIRMED

    def test_mark_returned(self) -> None:
        dm = DeliveryMetadata.create(
            method=DeliveryMethod.POSTAL,
            recipient_name="Recipient",
            recipient_department="Dept",
            recipient_address="Address",
        )
        dm.mark_sent()
        dm.mark_returned("Wrong address")
        assert dm.status == DeliveryStatus.RETURNED
        assert dm.notes == "Wrong address"

    def test_mark_failed(self) -> None:
        dm = DeliveryMetadata.create(
            method=DeliveryMethod.FAX,
            recipient_name="Recipient",
            recipient_department="Dept",
            recipient_address="Address",
        )
        dm.mark_failed("Line busy")
        assert dm.status == DeliveryStatus.FAILED


class TestSignatureMetadata:
    def test_create(self) -> None:
        sig = SignatureMetadata.create(
            user_id="user-1",
            full_name="Ali Ahmed",
            title="Director",
            department="MOH",
        )
        assert sig.user_id == "user-1"
        assert sig.full_name == "Ali Ahmed"
        assert not sig.is_digital
        assert not sig.is_verified

    def test_create_digital(self) -> None:
        sig = SignatureMetadata.create(
            user_id="user-2",
            full_name="Sara Ali",
            title="Manager",
            department="MOE",
            is_digital=True,
        )
        assert sig.is_digital

    def test_display_name(self) -> None:
        sig = SignatureMetadata.create(
            user_id="u1",
            full_name="Ali Ahmed",
            title="Director",
            department="MOH",
        )
        assert sig.display_name == "Ali Ahmed (Director)"


class TestReviewAssignment:
    def test_create(self) -> None:
        ra = ReviewAssignment.create(
            reviewer_id="user-2",
            reviewer_name="Sara Ali",
            reviewer_title="Manager",
            assigned_by="user-1",
        )
        assert ra.reviewer_id == "user-2"
        assert ra.is_current
        assert ra.completed_at is None

    def test_complete(self) -> None:
        ra = ReviewAssignment.create(
            reviewer_id="user-2",
            reviewer_name="Sara Ali",
            reviewer_title="Manager",
            assigned_by="user-1",
        )
        ra.complete("APPROVE", "Looks good")
        assert ra.action == "APPROVE"
        assert ra.notes == "Looks good"
        assert ra.completed_at is not None
        assert not ra.is_current


class TestRoutingStep:
    def test_create(self) -> None:
        rs = RoutingStep.create(
            from_department="DeptA",
            from_user="user-1",
            to_department="DeptB",
            to_user="user-2",
            action="FORWARD",
        )
        assert rs.action == "FORWARD"
        assert rs.routed_at is not None
        assert rs.completed_at is None

    def test_create_with_notes(self) -> None:
        rs = RoutingStep.create(
            from_department="DeptA",
            from_user="user-1",
            to_department="DeptB",
            to_user="user-2",
            action="FORWARD",
            notes="Please review urgently",
        )
        assert rs.notes == "Please review urgently"
