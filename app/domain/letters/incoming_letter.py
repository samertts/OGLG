from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.letters.events import LetterCreated
from app.domain.letters.letter import Letter, LetterType
from app.domain.letters.letter_classification import LetterClassification
from app.domain.letters.letter_priority import LetterPriority
from app.domain.letters.letter_status import LetterStatus


@dataclass
class IncomingLetter(Letter):
    received_date: datetime | None = None
    incoming_number: str | None = None
    assigned_to: str | None = None
    response_deadline: datetime | None = None
    incoming_document_ref: str | None = None

    @staticmethod
    def create(
        subject: str,
        body: str,
        sender_id: str,
        sender_name: str,
        sender_department: str,
        department_id: str,
        created_by_id: str,
        priority: LetterPriority = LetterPriority.NORMAL,
        classification: LetterClassification = LetterClassification.INTERNAL,
        language: str = "AR",
        received_date: datetime | None = None,
        incoming_number: str | None = None,
        assigned_to: str | None = None,
        response_deadline: datetime | None = None,
        incoming_document_ref: str | None = None,
    ) -> IncomingLetter:
        import uuid
        letter = IncomingLetter(
            id=str(uuid.uuid4()),
            letter_type=LetterType.INCOMING.value,
            subject=subject,
            body=body,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_department=sender_department,
            department_id=department_id,
            created_by_id=created_by_id,
            priority=priority,
            classification=classification,
            language=language,
            received_date=received_date or datetime.now(),
            incoming_number=incoming_number,
            assigned_to=assigned_to,
            response_deadline=response_deadline,
            incoming_document_ref=incoming_document_ref,
        )
        letter._events.append(
            LetterCreated.create(
                letter.id,
                created_by_id,
                {
                    "letter_type": LetterType.INCOMING,
                    "subject": subject,
                    "priority": priority.value,
                    "classification": classification.value,
                },
            )
        )
        return letter

    def assign_to(self, user_id: str) -> None:
        self.assigned_to = user_id
        self.updated_by_id = user_id
        self.updated_at = datetime.now()

    @property
    def is_overdue(self) -> bool:
        if self.response_deadline and self.status not in (LetterStatus.RECEIVED, LetterStatus.ARCHIVED):
            return datetime.now() > self.response_deadline
        return False
