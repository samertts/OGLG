from __future__ import annotations

import pytest

from app.domain.letters.exceptions import (
    ArchiveOperationError,
    LetterDomainError,
    LetterInvariantError,
    StateTransitionError,
)


class TestLetterDomainError:
    def test_base_exception(self) -> None:
        err = LetterDomainError("test message", code="TEST")
        assert err.message == "test message"
        assert err.code == "TEST"
        assert str(err) == "test message"

    def test_base_exception_no_code(self) -> None:
        err = LetterDomainError("test message")
        assert err.message == "test message"
        assert err.code is None

    def test_is_exception_subclass(self) -> None:
        assert issubclass(LetterDomainError, Exception)


class TestStateTransitionError:
    def test_transition_error(self) -> None:
        err = StateTransitionError("DRAFT", "APPROVED")
        assert err.from_status == "DRAFT"
        assert err.to_status == "APPROVED"
        assert err.reason == ""
        assert str(err) == "Cannot transition from DRAFT to APPROVED"

    def test_transition_error_with_reason(self) -> None:
        err = StateTransitionError("DRAFT", "SENT", "Direct send not allowed")
        assert err.reason == "Direct send not allowed"
        assert str(err) == "Cannot transition from DRAFT to SENT: Direct send not allowed"

    def test_is_domain_error_subclass(self) -> None:
        assert issubclass(StateTransitionError, LetterDomainError)

    def test_code(self) -> None:
        err = StateTransitionError("A", "B")
        assert err.code == "STATE_TRANSITION_ERROR"


class TestLetterInvariantError:
    def test_invariant_error(self) -> None:
        err = LetterInvariantError("letter-1", "Cannot edit letter in status: DELETED")
        assert err.letter_id == "letter-1"
        assert err.invariant == "Cannot edit letter in status: DELETED"
        assert str(err) == "Invariant violation on letter letter-1: Cannot edit letter in status: DELETED"

    def test_is_domain_error_subclass(self) -> None:
        assert issubclass(LetterInvariantError, LetterDomainError)

    def test_code(self) -> None:
        err = LetterInvariantError("l-1", "test")
        assert err.code == "INVARIANT_ERROR"


class TestArchiveOperationError:
    def test_archive_error(self) -> None:
        err = ArchiveOperationError("letter-1", "archive", "Already archived")
        assert err.letter_id == "letter-1"
        assert err.operation == "archive"
        assert err.reason == "Already archived"
        assert str(err) == "Cannot archive letter letter-1: Already archived"

    def test_restore_error(self) -> None:
        err = ArchiveOperationError("letter-2", "restore", "Letter is active")
        assert err.operation == "restore"
        assert str(err) == "Cannot restore letter letter-2: Letter is active"

    def test_is_domain_error_subclass(self) -> None:
        assert issubclass(ArchiveOperationError, LetterDomainError)

    def test_code(self) -> None:
        err = ArchiveOperationError("l-1", "archive", "test")
        assert err.code == "ARCHIVE_OPERATION_ERROR"

    def test_raised_and_caught(self) -> None:
        with pytest.raises(ArchiveOperationError) as excinfo:
            raise ArchiveOperationError("l-1", "purge", "Retention period not met")
        assert excinfo.value.operation == "purge"
        assert "Retention period not met" in str(excinfo.value)
