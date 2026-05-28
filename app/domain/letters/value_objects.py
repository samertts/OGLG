"""Backward-compatible re-exports for the refactored domain layer.

Value objects have been moved to individual files:
  - attachment.py: Attachment
  - signature_metadata.py: Signature (now SignatureMetadata)
  - delivery_metadata.py: DeliveryMetadata
  - document_reference.py: LetterNumber (now DocumentReference)
  - correspondence_party.py: CorrespondenceParty
  - review_assignment.py: ReviewAssignment
  - routing_step.py: RoutingStep
"""

from app.domain.letters.attachment import Attachment
from app.domain.letters.correspondence_party import CorrespondenceParty
from app.domain.letters.delivery_metadata import DeliveryMetadata
from app.domain.letters.document_reference import DocumentReference as LetterNumber
from app.domain.letters.review_assignment import ReviewAssignment
from app.domain.letters.routing_step import RoutingStep
from app.domain.letters.signature_metadata import SignatureMetadata as Signature

__all__ = [
    "Attachment",
    "CorrespondenceParty",
    "DeliveryMetadata",
    "LetterNumber",
    "ReviewAssignment",
    "RoutingStep",
    "Signature",
]
