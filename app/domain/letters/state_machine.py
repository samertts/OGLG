"""Letter state machine — re-exports from centralized exceptions and validators.

Backward-compatible re-export layer. New code should import directly from
app.domain.letters.exceptions and app.domain.letters.validators.
"""

from app.domain.letters.exceptions import StateTransitionError
from app.domain.letters.validators import (
    is_archivable,
    is_editable,
    is_reviewable,
    is_terminal,
    validate_archive_transition,
    validate_lifecycle_transition,
)

__all__ = [
    "StateTransitionError",
    "is_archivable",
    "is_editable",
    "is_reviewable",
    "is_terminal",
    "validate_archive_transition",
    "validate_lifecycle_transition",
]
