from __future__ import annotations

from app.application.letters.validation_service import LetterValidationService, ValidationResult
from app.domain.letters.enums import LetterStatus, LetterType


class TestLetterValidationService:
    def setup_method(self) -> None:
        self.validator = LetterValidationService()

    def test_validate_create_valid(self) -> None:
        result = self.validator.validate_create(
            LetterType.OUTGOING,
            "Valid Subject",
            "Valid body content",
            "user-1",
            "Ali Ahmed",
            "MOH",
            "dept-1",
            "user-1",
        )
        assert result.is_valid

    def test_validate_create_empty_subject(self) -> None:
        result = self.validator.validate_create(
            LetterType.OUTGOING,
            "",
            "Body",
            "user-1",
            "Ali",
            "Dept",
            "dept-1",
            "user-1",
        )
        assert not result.is_valid
        assert any(e.field == "subject" for e in result.errors)

    def test_validate_create_short_subject(self) -> None:
        result = self.validator.validate_create(
            LetterType.OUTGOING,
            "AB",
            "Body",
            "user-1",
            "Ali",
            "Dept",
            "dept-1",
            "user-1",
        )
        assert not result.is_valid
        assert any("at least" in e.message for e in result.errors)

    def test_validate_create_empty_body(self) -> None:
        result = self.validator.validate_create(
            LetterType.OUTGOING,
            "Subject",
            "",
            "user-1",
            "Ali",
            "Dept",
            "dept-1",
            "user-1",
        )
        assert not result.is_valid
        assert any(e.field == "body" for e in result.errors)

    def test_validate_create_missing_sender(self) -> None:
        result = self.validator.validate_create(
            LetterType.OUTGOING,
            "Subject",
            "Body",
            "",
            "",
            "",
            "dept-1",
            "user-1",
        )
        assert not result.is_valid
        assert any(e.field == "sender_id" for e in result.errors)
        assert any(e.field == "sender_name" for e in result.errors)

    def test_validate_edit_allowed(self) -> None:
        result = self.validator.validate_edit(LetterStatus.DRAFT)
        assert result.is_valid

    def test_validate_edit_not_allowed(self) -> None:
        result = self.validator.validate_edit(LetterStatus.APPROVED)
        assert not result.is_valid

    def test_validate_transition_valid(self) -> None:
        result = self.validator.validate_transition(LetterStatus.DRAFT, LetterStatus.PENDING_REVIEW)
        assert result.is_valid

    def test_validate_transition_invalid(self) -> None:
        result = self.validator.validate_transition(LetterStatus.DRAFT, LetterStatus.SENT)
        assert not result.is_valid

    def test_validate_attachment_pdf(self) -> None:
        result = self.validator.validate_attachment("doc.pdf", 1024, "application/pdf")
        assert result.is_valid

    def test_validate_attachment_invalid_extension(self) -> None:
        result = self.validator.validate_attachment("virus.exe", 1024, "application/x-msdownload")
        assert not result.is_valid
        assert any(e.field == "extension" for e in result.errors)

    def test_validate_attachment_zero_size(self) -> None:
        result = self.validator.validate_attachment("doc.pdf", 0, "application/pdf")
        assert not result.is_valid
        assert any(e.field == "file_size" for e in result.errors)

    def test_validate_attachment_too_large(self) -> None:
        max_size = 51 * 1024 * 1024
        result = self.validator.validate_attachment("doc.pdf", max_size, "application/pdf")
        assert not result.is_valid

    def test_validate_number_valid(self) -> None:
        result = self.validator.validate_number("MOH-2026-000001")
        assert result.is_valid

    def test_validate_number_none(self) -> None:
        result = self.validator.validate_number(None)
        assert result.is_valid

    def test_validate_number_invalid(self) -> None:
        result = self.validator.validate_number("invalid")
        assert not result.is_valid

    def test_validate_department_code_valid(self) -> None:
        result = self.validator.validate_department_code("MOH")
        assert result.is_valid

    def test_validate_department_code_empty(self) -> None:
        result = self.validator.validate_department_code("")
        assert not result.is_valid

    def test_validate_department_code_too_long(self) -> None:
        result = self.validator.validate_department_code("ABCDEFGHIJK")
        assert not result.is_valid

    def test_validation_result_raise_if_invalid(self) -> None:
        result = ValidationResult()
        result.add_error("test", "error message")
        assert not result.is_valid
        import pytest
        with pytest.raises(Exception):
            result.raise_if_invalid()

    def test_validation_result_empty(self) -> None:
        result = ValidationResult()
        assert result.is_valid
        assert len(result.errors) == 0
