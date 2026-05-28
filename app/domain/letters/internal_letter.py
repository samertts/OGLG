from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.letters.correspondence_party import CorrespondenceParty
from app.domain.letters.events import LetterCreated
from app.domain.letters.letter import Letter, LetterType
from app.domain.letters.letter_classification import LetterClassification
from app.domain.letters.letter_priority import LetterPriority


@dataclass
class InternalLetter(Letter):
    circulation_list: list[CorrespondenceParty] = field(default_factory=list)
    from_department: str = ""
    to_department: str = ""
    internal_deadline: datetime | None = None
    requires_acknowledgment: bool = False
    acknowledgment_received: bool = False

    @staticmethod
    def create(
        subject: str,
        body: str,
        sender_id: str,
        sender_name: str,
        sender_department: str,
        department_id: str,
        created_by_id: str,
        to_department: str = "",
        from_department: str = "",
        priority: LetterPriority = LetterPriority.NORMAL,
        classification: LetterClassification = LetterClassification.INTERNAL,
        language: str = "AR",
        requires_acknowledgment: bool = False,
        internal_deadline: datetime | None = None,
    ) -> InternalLetter:
        import uuid
        letter = InternalLetter(
            id=str(uuid.uuid4()),
            letter_type=LetterType.INTERNAL.value,
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
            to_department=to_department,
            from_department=from_department or sender_department,
            requires_acknowledgment=requires_acknowledgment,
            internal_deadline=internal_deadline,
        )
        letter._events.append(
            LetterCreated.create(
                letter.id,
                created_by_id,
                {
                    "letter_type": LetterType.INTERNAL,
                    "subject": subject,
                    "priority": priority.value,
                    "classification": classification.value,
                    "from_department": letter.from_department,
                    "to_department": to_department,
                },
            )
        )
        return letter

    def add_to_circulation(self, party: CorrespondenceParty) -> None:
        if party.id not in [p.id for p in self.circulation_list]:
            self.circulation_list.append(party)

    def remove_from_circulation(self, party_id: str) -> None:
        self.circulation_list = [p for p in self.circulation_list if p.id != party_id]

    def acknowledge(self, user_id: str) -> None:
        self.acknowledgment_received = True
        self.updated_by_id = user_id
        self.updated_at = datetime.now()

    @property
    def circulation_count(self) -> int:
        return len(self.circulation_list)

    @property
    def is_acknowledgment_pending(self) -> bool:
        return self.requires_acknowledgment and not self.acknowledgment_received
