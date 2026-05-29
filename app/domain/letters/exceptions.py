"""Domain exception hierarchy for the letter management system."""


class LetterDomainError(Exception):
    """Base exception for all letter domain errors."""

    def __init__(self, message: str, code: str | None = None) -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class StateTransitionError(LetterDomainError):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, from_status: str, to_status: str, reason: str = "") -> None:
        self.from_status = from_status
        self.to_status = to_status
        self.reason = reason
        msg = f"Cannot transition from {from_status} to {to_status}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, code="STATE_TRANSITION_ERROR")


class LetterInvariantError(LetterDomainError):
    """Raised when a domain invariant is violated."""

    def __init__(self, letter_id: str, invariant: str) -> None:
        self.letter_id = letter_id
        self.invariant = invariant
        msg = f"Invariant violation on letter {letter_id}: {invariant}"
        super().__init__(msg, code="INVARIANT_ERROR")


class ArchiveOperationError(LetterDomainError):
    """Raised when an archive/restore operation violates domain rules."""

    def __init__(self, letter_id: str, operation: str, reason: str) -> None:
        self.letter_id = letter_id
        self.operation = operation
        self.reason = reason
        msg = f"Cannot {operation} letter {letter_id}: {reason}"
        super().__init__(msg, code="ARCHIVE_OPERATION_ERROR")


__all__ = [
    "ArchiveOperationError",
    "LetterDomainError",
    "LetterInvariantError",
    "StateTransitionError",
]
