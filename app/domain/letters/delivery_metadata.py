from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.letters.delivery_status import DeliveryMethod, DeliveryStatus


@dataclass
class DeliveryMetadata:
    method: DeliveryMethod
    recipient_name: str
    recipient_department: str
    recipient_address: str
    status: DeliveryStatus = DeliveryStatus.PENDING
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    confirmed_by: str | None = None
    tracking_number: str | None = None
    notes: str = ""
    proof_of_delivery: str | None = None

    @staticmethod
    def create(
        method: DeliveryMethod,
        recipient_name: str,
        recipient_department: str,
        recipient_address: str,
    ) -> DeliveryMetadata:
        return DeliveryMetadata(
            method=method,
            recipient_name=recipient_name,
            recipient_department=recipient_department,
            recipient_address=recipient_address,
        )

    def mark_sent(self) -> None:
        self.status = DeliveryStatus.IN_TRANSIT
        self.sent_at = datetime.now()

    def mark_delivered(self, confirmed_by: str, proof: str | None = None) -> None:
        self.status = DeliveryStatus.DELIVERED
        self.delivered_at = datetime.now()
        self.confirmed_by = confirmed_by
        self.proof_of_delivery = proof

    def mark_confirmed(self) -> None:
        self.status = DeliveryStatus.CONFIRMED

    def mark_returned(self, reason: str = "") -> None:
        self.status = DeliveryStatus.RETURNED
        self.notes = reason

    def mark_failed(self, reason: str = "") -> None:
        self.status = DeliveryStatus.FAILED
        self.notes = reason
