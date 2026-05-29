from __future__ import annotations

import pytest

from app.domain.letters.archive_state import ArchiveState
from app.domain.letters.exceptions import StateTransitionError
from app.domain.letters.letter_status import LetterStatus
from app.domain.letters.validators import (
    is_archivable,
    is_editable,
    is_reviewable,
    is_terminal,
    validate_archive_transition,
    validate_lifecycle_transition,
)


class TestLifecycleTransitions:
    def test_draft_to_pending_review(self) -> None:
        validate_lifecycle_transition(LetterStatus.DRAFT, LetterStatus.PENDING_REVIEW)

    def test_draft_to_deleted(self) -> None:
        validate_lifecycle_transition(LetterStatus.DRAFT, LetterStatus.DELETED)

    def test_draft_to_approved_fails(self) -> None:
        with pytest.raises(StateTransitionError):
            validate_lifecycle_transition(LetterStatus.DRAFT, LetterStatus.APPROVED)

    def test_pending_review_to_in_review(self) -> None:
        validate_lifecycle_transition(LetterStatus.PENDING_REVIEW, LetterStatus.IN_REVIEW)

    def test_in_review_to_approved(self) -> None:
        validate_lifecycle_transition(LetterStatus.IN_REVIEW, LetterStatus.APPROVED)

    def test_in_review_to_rejected(self) -> None:
        validate_lifecycle_transition(LetterStatus.IN_REVIEW, LetterStatus.REJECTED)

    def test_approved_to_sent(self) -> None:
        validate_lifecycle_transition(LetterStatus.APPROVED, LetterStatus.SENT)

    def test_approved_to_archived(self) -> None:
        validate_lifecycle_transition(LetterStatus.APPROVED, LetterStatus.ARCHIVED)

    def test_rejected_to_draft(self) -> None:
        validate_lifecycle_transition(LetterStatus.REJECTED, LetterStatus.DRAFT)

    def test_sent_to_delivered(self) -> None:
        validate_lifecycle_transition(LetterStatus.SENT, LetterStatus.DELIVERED)

    def test_delivered_to_archived(self) -> None:
        validate_lifecycle_transition(LetterStatus.DELIVERED, LetterStatus.ARCHIVED)

    def test_archived_to_restored(self) -> None:
        validate_lifecycle_transition(LetterStatus.ARCHIVED, LetterStatus.RESTORED)

    def test_restored_to_draft(self) -> None:
        validate_lifecycle_transition(LetterStatus.RESTORED, LetterStatus.DRAFT)

    def test_deleted_has_no_transitions(self) -> None:
        with pytest.raises(StateTransitionError):
            validate_lifecycle_transition(LetterStatus.DELETED, LetterStatus.DRAFT)

    def test_direct_draft_to_sent_fails(self) -> None:
        with pytest.raises(StateTransitionError):
            validate_lifecycle_transition(LetterStatus.DRAFT, LetterStatus.SENT)

    def test_state_transition_error_from_validator(self) -> None:
        with pytest.raises(StateTransitionError) as excinfo:
            validate_lifecycle_transition(LetterStatus.DRAFT, LetterStatus.SENT)
        assert excinfo.value.from_status == "DRAFT"
        assert excinfo.value.to_status == "SENT"
        assert "Cannot transition from DRAFT to SENT" in str(excinfo.value)


class TestHelperFunctions:
    def test_is_terminal(self) -> None:
        assert is_terminal(LetterStatus.DELETED)
        assert not is_terminal(LetterStatus.DRAFT)

    def test_is_editable(self) -> None:
        assert is_editable(LetterStatus.DRAFT)
        assert is_editable(LetterStatus.RESTORED)
        assert not is_editable(LetterStatus.APPROVED)
        assert not is_editable(LetterStatus.ARCHIVED)

    def test_is_archivable(self) -> None:
        assert is_archivable(LetterStatus.APPROVED)
        assert is_archivable(LetterStatus.SENT)
        assert is_archivable(LetterStatus.DELIVERED)
        assert is_archivable(LetterStatus.RESTORED)
        assert not is_archivable(LetterStatus.DRAFT)

    def test_is_reviewable(self) -> None:
        assert is_reviewable(LetterStatus.PENDING_REVIEW)
        assert is_reviewable(LetterStatus.IN_REVIEW)
        assert not is_reviewable(LetterStatus.DRAFT)


class TestArchiveTransitions:
    def test_active_to_archived(self) -> None:
        validate_archive_transition(ArchiveState.ACTIVE, ArchiveState.ARCHIVED)

    def test_active_to_soft_deleted(self) -> None:
        validate_archive_transition(ArchiveState.ACTIVE, ArchiveState.SOFT_DELETED)

    def test_soft_deleted_to_active(self) -> None:
        validate_archive_transition(ArchiveState.SOFT_DELETED, ArchiveState.ACTIVE)

    def test_archived_to_active(self) -> None:
        validate_archive_transition(ArchiveState.ARCHIVED, ArchiveState.ACTIVE)

    def test_purged_has_no_transitions(self) -> None:
        with pytest.raises(StateTransitionError):
            validate_archive_transition(ArchiveState.PURGED, ArchiveState.ACTIVE)

    def test_active_to_purged_fails(self) -> None:
        with pytest.raises(StateTransitionError):
            validate_archive_transition(ArchiveState.ACTIVE, ArchiveState.PURGED)
