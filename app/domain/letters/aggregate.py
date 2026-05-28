from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.letters.enums import (
    ArchiveStatus,
    LetterClassification,
    LetterPriority,
    LetterStatus,
    LetterType,
)
from app.domain.letters.events import (
    DomainEvent,
    LetterApproved,
    LetterArchived,
    LetterCreated,
    LetterDeleted,
    LetterEdited,
    LetterNumberAssigned,
    LetterPrinted,
    LetterRejected,
    LetterRestored,
    LetterSubmitted,
)
from app.domain.letters.state_machine import (
    is_editable,
    validate_archive_transition,
    validate_lifecycle_transition,
)
from app.domain.letters.value_objects import (
    Attachment,
    DeliveryMetadata,
    ReviewAssignment,
    RoutingStep,
    Signature,
)


@dataclass
class LetterAggregate:
    id: str
    letter_type: LetterType
    status: LetterStatus = LetterStatus.DRAFT
    archive_status: ArchiveStatus = ArchiveStatus.ACTIVE
    number: str | None = None
    subject: str = ""
    body: str = ""
    sender_id: str = ""
    sender_name: str = ""
    sender_department: str = ""
    recipient_id: str | None = None
    recipient_name: str = ""
    recipient_department: str = ""
    recipient_address: str = ""
    priority: LetterPriority = LetterPriority.NORMAL
    classification: LetterClassification = LetterClassification.INTERNAL
    department_id: str = ""
    reference_number: str | None = None
    language: str = "AR"
    created_by_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_by_id: str | None = None
    updated_at: datetime | None = None
    is_archived: bool = False
    archived_at: datetime | None = None
    archived_by_id: str | None = None
    deleted_at: datetime | None = None
    deleted_by_id: str | None = None
    version: int = 1
    attachments: list[Attachment] = field(default_factory=list)
    signatures: list[Signature] = field(default_factory=list)
    delivery: DeliveryMetadata | None = None
    reviews: list[ReviewAssignment] = field(default_factory=list)
    routing_history: list[RoutingStep] = field(default_factory=list)
    _events: list[DomainEvent] = field(default_factory=list, repr=False)

    @staticmethod
    def create(
        letter_type: LetterType,
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
        recipient_name: str = "",
        recipient_department: str = "",
        recipient_address: str = "",
        recipient_id: str | None = None,
        reference_number: str | None = None,
    ) -> LetterAggregate:
        import uuid

        letter = LetterAggregate(
            id=str(uuid.uuid4()),
            letter_type=letter_type,
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
            recipient_name=recipient_name,
            recipient_department=recipient_department,
            recipient_address=recipient_address,
            recipient_id=recipient_id,
            reference_number=reference_number,
        )
        letter._events.append(
            LetterCreated.create(
                letter.id,
                created_by_id,
                {
                    "letter_type": letter_type.value,
                    "subject": subject,
                    "priority": priority.value,
                    "classification": classification.value,
                },
            )
        )
        return letter

    def edit(self, user_id: str, subject: str | None = None, body: str | None = None, priority: LetterPriority | None = None, classification: LetterClassification | None = None, recipient_name: str | None = None, recipient_department: str | None = None, recipient_address: str | None = None) -> None:
        if not is_editable(self.status):
            raise ValueError(f"Cannot edit letter in status: {self.status.value}")
        changes: dict[str, Any] = {}
        if subject is not None and subject != self.subject:
            changes["subject"] = {"old": self.subject, "new": subject}
            self.subject = subject
        if body is not None and body != self.body:
            changes["body"] = {"old_length": len(self.body), "new_length": len(body)}
            self.body = body
        if priority is not None and priority != self.priority:
            changes["priority"] = {"old": self.priority.value, "new": priority.value}
            self.priority = priority
        if classification is not None and classification != self.classification:
            changes["classification"] = {"old": self.classification.value, "new": classification.value}
            self.classification = classification
        if recipient_name is not None:
            changes["recipient_name"] = {"old": self.recipient_name, "new": recipient_name}
            self.recipient_name = recipient_name
        if recipient_department is not None:
            changes["recipient_department"] = {"old": self.recipient_department, "new": recipient_department}
            self.recipient_department = recipient_department
        if recipient_address is not None:
            changes["recipient_address"] = {"old": self.recipient_address, "new": recipient_address}
            self.recipient_address = recipient_address
        self.updated_by_id = user_id
        self.updated_at = datetime.now()
        self.version += 1
        if changes:
            self._events.append(LetterEdited.create(self.id, user_id, changes))

    def submit_for_review(self, user_id: str) -> None:
        validate_lifecycle_transition(self.status, LetterStatus.PENDING_REVIEW)
        self.status = LetterStatus.PENDING_REVIEW
        self.updated_by_id = user_id
        self.updated_at = datetime.now()
        self._events.append(LetterSubmitted.create(self.id, user_id))

    def start_review(self, user_id: str) -> None:
        validate_lifecycle_transition(self.status, LetterStatus.IN_REVIEW)
        self.status = LetterStatus.IN_REVIEW
        self.updated_by_id = user_id
        self.updated_at = datetime.now()

    def approve(self, user_id: str, reviewer_id: str, notes: str = "") -> None:
        validate_lifecycle_transition(self.status, LetterStatus.APPROVED)
        self.status = LetterStatus.APPROVED
        self.updated_by_id = user_id
        self.updated_at = datetime.now()
        self._complete_current_review(reviewer_id, "APPROVE", notes)
        self._events.append(LetterApproved.create(self.id, user_id, reviewer_id, notes))

    def return_to_draft(self, user_id: str) -> None:
        validate_lifecycle_transition(self.status, LetterStatus.DRAFT)
        self.status = LetterStatus.DRAFT
        self.updated_by_id = user_id
        self.updated_at = datetime.now()

    def reject(self, user_id: str, reviewer_id: str, reason: str) -> None:
        validate_lifecycle_transition(self.status, LetterStatus.REJECTED)
        self.status = LetterStatus.REJECTED
        self.updated_by_id = user_id
        self.updated_at = datetime.now()
        self._complete_current_review(reviewer_id, "REJECT", reason)
        self._events.append(LetterRejected.create(self.id, user_id, reviewer_id, reason))

    def assign_number(self, number: str, user_id: str) -> None:
        self.number = number
        self.updated_by_id = user_id
        self.updated_at = datetime.now()
        self._events.append(LetterNumberAssigned.create(self.id, user_id, number))

    def mark_sent(self, user_id: str) -> None:
        validate_lifecycle_transition(self.status, LetterStatus.SENT)
        self.status = LetterStatus.SENT
        self.updated_by_id = user_id
        self.updated_at = datetime.now()

    def mark_delivered(self, user_id: str, proof: str | None = None) -> None:
        validate_lifecycle_transition(self.status, LetterStatus.DELIVERED)
        self.status = LetterStatus.DELIVERED
        self.updated_by_id = user_id
        self.updated_at = datetime.now()
        if self.delivery:
            self.delivery.delivered_at = datetime.now()
            self.delivery.confirmed_by = user_id
            self.delivery.proof_of_delivery = proof

    def mark_received(self, user_id: str) -> None:
        validate_lifecycle_transition(self.status, LetterStatus.RECEIVED)
        self.status = LetterStatus.RECEIVED
        self.updated_by_id = user_id
        self.updated_at = datetime.now()

    def archive(self, user_id: str, reason: str = "") -> None:
        validate_lifecycle_transition(self.status, LetterStatus.ARCHIVED)
        validate_archive_transition(self.archive_status, ArchiveStatus.ARCHIVED)
        self.status = LetterStatus.ARCHIVED
        self.archive_status = ArchiveStatus.ARCHIVED
        self.is_archived = True
        self.archived_at = datetime.now()
        self.archived_by_id = user_id
        self.updated_by_id = user_id
        self.updated_at = datetime.now()
        self._events.append(LetterArchived.create(self.id, user_id, reason))

    def restore(self, user_id: str, reason: str = "") -> None:
        validate_lifecycle_transition(self.status, LetterStatus.RESTORED)
        validate_archive_transition(self.archive_status, ArchiveStatus.ACTIVE)
        self.status = LetterStatus.RESTORED
        self.archive_status = ArchiveStatus.ACTIVE
        self.is_archived = False
        self.updated_by_id = user_id
        self.updated_at = datetime.now()
        self._events.append(LetterRestored.create(self.id, user_id, reason))

    def soft_delete(self, user_id: str, reason: str = "") -> None:
        validate_lifecycle_transition(self.status, LetterStatus.DELETED)
        validate_archive_transition(self.archive_status, ArchiveStatus.SOFT_DELETED)
        self.status = LetterStatus.DELETED
        self.archive_status = ArchiveStatus.SOFT_DELETED
        self.deleted_at = datetime.now()
        self.deleted_by_id = user_id
        self.updated_by_id = user_id
        self.updated_at = datetime.now()
        self._events.append(LetterDeleted.create(self.id, user_id, reason))

    def add_attachment(self, attachment: Attachment) -> None:
        self.attachments.append(attachment)

    def remove_attachment(self, attachment_id: str) -> None:
        self.attachments = [a for a in self.attachments if a.id != attachment_id]

    def record_print(self, user_id: str, copies: int = 1) -> None:
        self._events.append(LetterPrinted.create(self.id, user_id, copies))

    def add_review(self, reviewer_id: str, reviewer_name: str, reviewer_title: str, assigned_by: str) -> None:
        import uuid

        for review in self.reviews:
            review.is_current = False
        assignment = ReviewAssignment(
            id=str(uuid.uuid4()),
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            reviewer_title=reviewer_title,
            assigned_at=datetime.now(),
            is_current=True,
        )
        self.reviews.append(assignment)

    def _complete_current_review(self, reviewer_id: str, action: str, notes: str) -> None:
        for review in self.reviews:
            if review.is_current and review.reviewer_id == reviewer_id:
                review.completed_at = datetime.now()
                review.action = action
                review.notes = notes
                review.is_current = False
                break

    def add_routing_step(self, step: RoutingStep) -> None:
        self.routing_history.append(step)

    def set_delivery(self, delivery: DeliveryMetadata) -> None:
        self.delivery = delivery

    @property
    def current_reviewer(self) -> ReviewAssignment | None:
        for review in self.reviews:
            if review.is_current:
                return review
        return None

    def pop_events(self) -> list[DomainEvent]:
        events = list(self._events)
        self._events.clear()
        return events
