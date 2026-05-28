from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LetterNumber:
    prefix: str
    year: int
    sequence: int

    def __str__(self) -> str:
        return f"{self.prefix}-{self.year}-{self.sequence:06d}"

    @staticmethod
    def parse(value: str) -> LetterNumber:
        parts = value.split("-")
        if len(parts) != 3:
            raise ValueError(f"Invalid letter number format: {value}")
        return LetterNumber(parts[0], int(parts[1]), int(parts[2]))

    @staticmethod
    def is_valid_format(value: str) -> bool:
        import re

        return bool(re.match(r"^[A-Za-z0-9]+-\d{4}-\d{6}$", value))


@dataclass(frozen=True)
class DepartmentCode:
    code: str
    name: str

    def __str__(self) -> str:
        return self.code


@dataclass
class Attachment:
    id: str
    filename: str
    original_name: str
    mime_type: str
    file_size: int
    extension: str
    sha256_hash: str
    storage_path: str
    uploaded_at: datetime
    uploaded_by: str
    description: str = ""
    is_encrypted: bool = False


@dataclass
class Signature:
    id: str
    user_id: str
    full_name: str
    title: str
    department: str
    signed_at: datetime
    signature_data: str | None = None
    is_digital: bool = False
    notes: str = ""


@dataclass
class DeliveryMetadata:
    method: str
    recipient_name: str
    recipient_department: str
    recipient_address: str
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    confirmed_by: str | None = None
    tracking_number: str | None = None
    notes: str = ""
    proof_of_delivery: str | None = None


@dataclass
class ReviewAssignment:
    id: str
    reviewer_id: str
    reviewer_name: str
    reviewer_title: str
    assigned_at: datetime
    completed_at: datetime | None = None
    action: str | None = None
    notes: str = ""
    is_current: bool = True


@dataclass
class RoutingStep:
    id: str
    from_department: str
    from_user: str
    to_department: str
    to_user: str
    routed_at: datetime
    action: str
    notes: str = ""
    completed_at: datetime | None = None
