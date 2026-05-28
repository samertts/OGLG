"""Domain layer: letter aggregate, state machines, value objects, and interfaces."""

from app.domain.letters.archive_state import ArchiveState
from app.domain.letters.attachment import Attachment
from app.domain.letters.correspondence_party import CorrespondenceParty
from app.domain.letters.delivery_metadata import DeliveryMetadata
from app.domain.letters.delivery_status import DeliveryMethod, DeliveryStatus
from app.domain.letters.document_reference import DocumentReference
from app.domain.letters.events import (
    DomainEvent,
    EventType,
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
from app.domain.letters.incoming_letter import IncomingLetter
from app.domain.letters.interfaces import (
    AttachmentRepository,
    AuditRepository,
    LetterData,
    LetterRepository,
    UnitOfWork,
)
from app.domain.letters.internal_letter import InternalLetter
from app.domain.letters.letter import Letter, LetterType
from app.domain.letters.letter_classification import LetterClassification
from app.domain.letters.letter_priority import LetterPriority
from app.domain.letters.letter_status import LetterStatus
from app.domain.letters.outgoing_letter import OutgoingLetter
from app.domain.letters.review_assignment import ReviewAssignment
from app.domain.letters.routing_step import RoutingStep
from app.domain.letters.signature_metadata import SignatureMetadata
from app.domain.letters.state_machine import (
    StateTransitionError,
    is_archivable,
    is_editable,
    is_reviewable,
    is_terminal,
    validate_archive_transition,
    validate_lifecycle_transition,
)

__all__ = [
    "ArchiveState",
    "Attachment",
    "AttachmentRepository",
    "AuditRepository",
    "CorrespondenceParty",
    "DeliveryMetadata",
    "DeliveryMethod",
    "DeliveryStatus",
    "DocumentReference",
    "DomainEvent",
    "EventType",
    "IncomingLetter",
    "InternalLetter",
    "Letter",
    "LetterApproved",
    "LetterArchived",
    "LetterClassification",
    "LetterCreated",
    "LetterDeleted",
    "LetterEdited",
    "LetterNumberAssigned",
    "LetterPrinted",
    "LetterPriority",
    "LetterRejected",
    "LetterRestored",
    "LetterStatus",
    "LetterSubmitted",
    "LetterData",
    "LetterRepository",
    "LetterType",
    "OutgoingLetter",
    "ReviewAssignment",
    "RoutingStep",
    "SignatureMetadata",
    "StateTransitionError",
    "UnitOfWork",
    "is_archivable",
    "is_editable",
    "is_reviewable",
    "is_terminal",
    "validate_archive_transition",
    "validate_lifecycle_transition",
]
