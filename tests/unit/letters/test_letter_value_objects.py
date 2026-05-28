from __future__ import annotations

from datetime import datetime

from app.domain.letters.value_objects import (
    Attachment,
    DeliveryMetadata,
    LetterNumber,
    ReviewAssignment,
    RoutingStep,
    Signature,
)


class TestLetterNumber:
    def test_str_format(self) -> None:
        num = LetterNumber("MOH", 2026, 1)
        assert str(num) == "MOH-2026-000001"

    def test_parse_valid(self) -> None:
        num = LetterNumber.parse("MOH-2026-000001")
        assert num.prefix == "MOH"
        assert num.year == 2026
        assert num.sequence == 1

    def test_parse_with_large_sequence(self) -> None:
        num = LetterNumber.parse("LAB-2026-000145")
        assert num.prefix == "LAB"
        assert num.sequence == 145

    def test_parse_invalid_format(self) -> None:
        import pytest
        with pytest.raises(ValueError):
            LetterNumber.parse("invalid")

    def test_is_valid_format(self) -> None:
        assert LetterNumber.is_valid_format("MOH-2026-000001")
        assert LetterNumber.is_valid_format("LAB-2026-000145")
        assert not LetterNumber.is_valid_format("invalid")
        assert not LetterNumber.is_valid_format("MOH-2026-001")
        assert not LetterNumber.is_valid_format("")

    def test_padding(self) -> None:
        num = LetterNumber("DEPT", 2026, 999999)
        assert str(num) == "DEPT-2026-999999"


class TestAttachment:
    def test_create(self) -> None:
        now = datetime.now()
        att = Attachment(
            id="att-1",
            filename="doc.pdf",
            original_name="report.pdf",
            mime_type="application/pdf",
            file_size=1024,
            extension=".pdf",
            sha256_hash="abc123",
            storage_path="/storage/doc.pdf",
            uploaded_at=now,
            uploaded_by="user-1",
        )
        assert att.id == "att-1"
        assert att.filename == "doc.pdf"
        assert att.file_size == 1024
        assert att.sha256_hash == "abc123"


class TestSignature:
    def test_create(self) -> None:
        now = datetime.now()
        sig = Signature(
            id="sig-1",
            user_id="user-1",
            full_name="Ali Ahmed",
            title="Director",
            department="MOH",
            signed_at=now,
        )
        assert sig.full_name == "Ali Ahmed"
        assert sig.is_digital is False


class TestDeliveryMetadata:
    def test_create(self) -> None:
        dm = DeliveryMetadata(
            method="COURIER",
            recipient_name="Ministry of Health",
            recipient_department="Procurement",
            recipient_address="Baghdad",
        )
        assert dm.method == "COURIER"
        assert dm.delivered_at is None


class TestReviewAssignment:
    def test_create(self) -> None:
        now = datetime.now()
        ra = ReviewAssignment(
            id="rev-1",
            reviewer_id="user-2",
            reviewer_name="Sara Ali",
            reviewer_title="Manager",
            assigned_at=now,
        )
        assert ra.is_current is True
        assert ra.completed_at is None


class TestRoutingStep:
    def test_create(self) -> None:
        now = datetime.now()
        rs = RoutingStep(
            id="route-1",
            from_department="DeptA",
            from_user="user-1",
            to_department="DeptB",
            to_user="user-2",
            routed_at=now,
            action="FORWARD",
        )
        assert rs.action == "FORWARD"
        assert rs.completed_at is None
