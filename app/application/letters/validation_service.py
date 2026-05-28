from __future__ import annotations

from app.domain.letters.enums import (
    LetterStatus,
    LetterType,
)
from app.domain.letters.state_machine import validate_lifecycle_transition
from app.domain.letters.value_objects import LetterNumber


class ValidationError(Exception):
    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class ValidationResult:
    def __init__(self) -> None:
        self._errors: list[ValidationError] = []

    def add_error(self, field: str, message: str) -> None:
        self._errors.append(ValidationError(field, message))

    @property
    def is_valid(self) -> bool:
        return len(self._errors) == 0

    @property
    def errors(self) -> list[ValidationError]:
        return list(self._errors)

    def raise_if_invalid(self) -> None:
        if not self.is_valid:
            raise ValidationError("validation", "; ".join(f"{e.field}: {e.message}" for e in self._errors))


class LetterValidationService:
    REQUIRED_FIELDS = {
        "subject": "Subject is required",
        "body": "Body is required",
        "sender_id": "Sender is required",
        "sender_name": "Sender name is required",
        "sender_department": "Sender department is required",
        "department_id": "Department is required",
        "created_by_id": "Creator is required",
    }

    MAX_SUBJECT_LENGTH = 500
    MAX_BODY_LENGTH = 100000
    MAX_RECIPIENT_NAME = 200
    MAX_DEPARTMENT_NAME = 200
    MAX_ADDRESS = 500
    ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png", ".tiff", ".zip"}
    MAX_FILE_SIZE = 50 * 1024 * 1024
    MAX_ATTACHMENTS = 20
    MIN_SUBJECT_LENGTH = 3

    def validate_create(self, letter_type: LetterType, subject: str, body: str, sender_id: str, sender_name: str, sender_department: str, department_id: str, created_by_id: str) -> ValidationResult:
        result = ValidationResult()
        if not subject or not subject.strip():
            result.add_error("subject", self.REQUIRED_FIELDS["subject"])
        elif len(subject) < self.MIN_SUBJECT_LENGTH:
            result.add_error("subject", f"Subject must be at least {self.MIN_SUBJECT_LENGTH} characters")
        elif len(subject) > self.MAX_SUBJECT_LENGTH:
            result.add_error("subject", f"Subject must not exceed {self.MAX_SUBJECT_LENGTH} characters")
        if not body or not body.strip():
            result.add_error("body", self.REQUIRED_FIELDS["body"])
        elif len(body) > self.MAX_BODY_LENGTH:
            result.add_error("body", f"Body must not exceed {self.MAX_BODY_LENGTH} characters")
        if not sender_id:
            result.add_error("sender_id", self.REQUIRED_FIELDS["sender_id"])
        if not sender_name or not sender_name.strip():
            result.add_error("sender_name", self.REQUIRED_FIELDS["sender_name"])
        if not sender_department or not sender_department.strip():
            result.add_error("sender_department", self.REQUIRED_FIELDS["sender_department"])
        if not department_id:
            result.add_error("department_id", self.REQUIRED_FIELDS["department_id"])
        if not created_by_id:
            result.add_error("created_by_id", self.REQUIRED_FIELDS["created_by_id"])
        return result

    def validate_edit(self, status: LetterStatus) -> ValidationResult:
        result = ValidationResult()
        from app.domain.letters.state_machine import is_editable

        if not is_editable(status):
            result.add_error("status", f"Cannot edit letter in status: {status.value}")
        return result

    def validate_transition(self, current: LetterStatus, target: LetterStatus) -> ValidationResult:
        result = ValidationResult()
        try:
            validate_lifecycle_transition(current, target)
        except Exception as exc:
            result.add_error("status", str(exc))
        return result

    def validate_attachment(self, filename: str, file_size: int, mime_type: str) -> ValidationResult:
        result = ValidationResult()
        import os

        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            result.add_error("extension", f"File extension '{ext}' is not allowed. Allowed: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}")
        if file_size <= 0:
            result.add_error("file_size", "File size must be greater than 0")
        if file_size > self.MAX_FILE_SIZE:
            max_mb = self.MAX_FILE_SIZE // (1024 * 1024)
            result.add_error("file_size", f"File size exceeds maximum of {max_mb}MB")
        if not mime_type:
            result.add_error("mime_type", "MIME type is required")
        return result

    def validate_number(self, number: str | None) -> ValidationResult:
        result = ValidationResult()
        if number is not None and number.strip():
            if not LetterNumber.is_valid_format(number):
                result.add_error("number", f"Invalid number format: {number}. Expected format: PREFIX-YYYY-SEQUENCE")
        return result

    def validate_search_query(self, query: str) -> ValidationResult:
        result = ValidationResult()
        if not query or not query.strip():
            result.add_error("query", "Search query cannot be empty")
        if len(query) > 200:
            result.add_error("query", "Search query must not exceed 200 characters")
        return result

    def validate_department_code(self, code: str) -> ValidationResult:
        result = ValidationResult()
        if not code or not code.strip():
            result.add_error("department_code", "Department code cannot be empty")
        if len(code) > 10:
            result.add_error("department_code", "Department code must not exceed 10 characters")
        if not code.isalnum():
            result.add_error("department_code", "Department code must be alphanumeric")
        return result
