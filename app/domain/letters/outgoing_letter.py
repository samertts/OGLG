from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.letters.delivery_metadata import DeliveryMetadata
from app.domain.letters.delivery_status import DeliveryStatus
from app.domain.letters.events import LetterCreated
from app.domain.letters.letter import Letter, LetterType
from app.domain.letters.letter_classification import LetterClassification
from app.domain.letters.letter_priority import LetterPriority


@dataclass
class OutgoingLetter(Letter):
    sent_date: datetime | None = None
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    tracking_number: str | None = None
    proof_of_delivery: str | None = None

    @staticmethod
    def create(
        subject: str,
        body: str,
        sender_id: str,
        sender_name: str,
        sender_department: str,
        department_id: str,
        created_by_id: str,
        recipient_name: str,
        recipient_department: str,
        recipient_address: str = "",
        recipient_id: str | None = None,
        priority: LetterPriority = LetterPriority.NORMAL,
        classification: LetterClassification = LetterClassification.INTERNAL,
        language: str = "AR",
        reference_number: str | None = None,
        delivery: DeliveryMetadata | None = None,
    ) -> OutgoingLetter:
        import uuid
        letter = OutgoingLetter(
            id=str(uuid.uuid4()),
            letter_type=LetterType.OUTGOING.value,
            subject=subject,
            body=body,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_department=sender_department,
            department_id=department_id,
            created_by_id=created_by_id,
            recipient_name=recipient_name,
            recipient_department=recipient_department,
            recipient_address=recipient_address,
            recipient_id=recipient_id,
            priority=priority,
            classification=classification,
            language=language,
            reference_number=reference_number,
            delivery=delivery,
        )
        letter._events.append(
            LetterCreated.create(
                letter.id,
                created_by_id,
                {
                    "letter_type": LetterType.OUTGOING,
                    "subject": subject,
                    "recipient": recipient_name,
                    "priority": priority.value,
                    "classification": classification.value,
                },
            )
        )
        return letter

    def mark_sent(self, user_id: str, tracking_number: str | None = None) -> None:
        super().mark_sent(user_id)
        self.sent_date = datetime.now()
        self.delivery_status = DeliveryStatus.IN_TRANSIT
        if tracking_number:
            self.tracking_number = tracking_number

    def mark_delivered(self, user_id: str, proof: str | None = None) -> None:
        super().mark_delivered(user_id, proof)
        self.delivery_status = DeliveryStatus.DELIVERED
        if proof:
            self.proof_of_delivery = proof

    @property
    def has_tracking(self) -> bool:
        return bool(self.tracking_number)

    @property
    def is_in_transit(self) -> bool:
        return self.delivery_status == DeliveryStatus.IN_TRANSIT
