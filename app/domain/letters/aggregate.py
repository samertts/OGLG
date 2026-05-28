"""Backward-compatible re-exports for the refactored domain layer.

LetterAggregate has been renamed to Letter and moved to letter.py.
Type-specific entities are in incoming_letter.py, outgoing_letter.py, internal_letter.py.
"""

from app.domain.letters.incoming_letter import IncomingLetter
from app.domain.letters.internal_letter import InternalLetter
from app.domain.letters.letter import Letter as LetterAggregate
from app.domain.letters.outgoing_letter import OutgoingLetter

__all__ = ["IncomingLetter", "InternalLetter", "LetterAggregate", "OutgoingLetter"]
