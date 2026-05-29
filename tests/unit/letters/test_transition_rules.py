from __future__ import annotations

import pytest

from app.application.letters.workflow_engine import (
    WORKFLOW_STATUSES,
    _ALLOWED_WORKFLOW_MATRIX,
)
from app.domain.letters.letter_status import LetterStatus


class TestWorkflowStatuses:
    def test_all_workflow_statuses_are_valid(self) -> None:
        for status in WORKFLOW_STATUSES:
            assert isinstance(status, LetterStatus)

    def test_workflow_status_count(self) -> None:
        assert len(WORKFLOW_STATUSES) == 8

    def test_draft_included(self) -> None:
        assert LetterStatus.DRAFT in WORKFLOW_STATUSES

    def test_under_review_is_in_review(self) -> None:
        assert LetterStatus.IN_REVIEW in WORKFLOW_STATUSES

    def test_deleted_included_as_cancelled(self) -> None:
        assert LetterStatus.DELETED in WORKFLOW_STATUSES

    def test_pending_review_not_in_workflow(self) -> None:
        assert LetterStatus.PENDING_REVIEW not in WORKFLOW_STATUSES

    def test_sent_not_in_workflow(self) -> None:
        assert LetterStatus.SENT not in WORKFLOW_STATUSES

    def test_received_not_in_workflow(self) -> None:
        assert LetterStatus.RECEIVED not in WORKFLOW_STATUSES


class TestTransitionMatrixCoverage:
    def test_all_statuses_have_entry(self) -> None:
        for status in WORKFLOW_STATUSES:
            assert status in _ALLOWED_WORKFLOW_MATRIX

    def test_no_extra_statuses_in_matrix(self) -> None:
        for status in _ALLOWED_WORKFLOW_MATRIX:
            assert status in WORKFLOW_STATUSES

    def test_deleted_is_terminal(self) -> None:
        assert len(_ALLOWED_WORKFLOW_MATRIX[LetterStatus.DELETED]) == 0


class TestValidTransitions:
    @pytest.mark.parametrize("from_status,to_status", [
        (LetterStatus.DRAFT, LetterStatus.IN_REVIEW),
        (LetterStatus.DRAFT, LetterStatus.DELETED),
        (LetterStatus.IN_REVIEW, LetterStatus.APPROVED),
        (LetterStatus.IN_REVIEW, LetterStatus.REJECTED),
        (LetterStatus.IN_REVIEW, LetterStatus.DRAFT),
        (LetterStatus.APPROVED, LetterStatus.DELIVERED),
        (LetterStatus.APPROVED, LetterStatus.ARCHIVED),
        (LetterStatus.REJECTED, LetterStatus.DRAFT),
        (LetterStatus.REJECTED, LetterStatus.DELETED),
        (LetterStatus.DELIVERED, LetterStatus.ARCHIVED),
        (LetterStatus.DELIVERED, LetterStatus.RESTORED),
        (LetterStatus.ARCHIVED, LetterStatus.RESTORED),
        (LetterStatus.ARCHIVED, LetterStatus.DELETED),
        (LetterStatus.RESTORED, LetterStatus.DRAFT),
        (LetterStatus.RESTORED, LetterStatus.ARCHIVED),
    ])
    def test_transition_is_allowed(self, from_status: LetterStatus, to_status: LetterStatus) -> None:
        allowed = _ALLOWED_WORKFLOW_MATRIX[from_status]
        assert to_status in allowed


class TestInvalidTransitions:
    @pytest.mark.parametrize("from_status,to_status", [
        (LetterStatus.DRAFT, LetterStatus.APPROVED),
        (LetterStatus.DRAFT, LetterStatus.REJECTED),
        (LetterStatus.DRAFT, LetterStatus.DELIVERED),
        (LetterStatus.DRAFT, LetterStatus.ARCHIVED),
        (LetterStatus.DRAFT, LetterStatus.RESTORED),
        (LetterStatus.IN_REVIEW, LetterStatus.DELIVERED),
        (LetterStatus.IN_REVIEW, LetterStatus.ARCHIVED),
        (LetterStatus.IN_REVIEW, LetterStatus.RESTORED),
        (LetterStatus.IN_REVIEW, LetterStatus.DELETED),
        (LetterStatus.APPROVED, LetterStatus.DRAFT),
        (LetterStatus.APPROVED, LetterStatus.REJECTED),
        (LetterStatus.APPROVED, LetterStatus.IN_REVIEW),
        (LetterStatus.APPROVED, LetterStatus.RESTORED),
        (LetterStatus.REJECTED, LetterStatus.APPROVED),
        (LetterStatus.REJECTED, LetterStatus.IN_REVIEW),
        (LetterStatus.REJECTED, LetterStatus.DELIVERED),
        (LetterStatus.REJECTED, LetterStatus.ARCHIVED),
        (LetterStatus.REJECTED, LetterStatus.RESTORED),
        (LetterStatus.DELIVERED, LetterStatus.DRAFT),
        (LetterStatus.DELIVERED, LetterStatus.APPROVED),
        (LetterStatus.DELIVERED, LetterStatus.REJECTED),
        (LetterStatus.DELIVERED, LetterStatus.IN_REVIEW),
        (LetterStatus.DELIVERED, LetterStatus.DELETED),
        (LetterStatus.ARCHIVED, LetterStatus.DRAFT),
        (LetterStatus.ARCHIVED, LetterStatus.APPROVED),
        (LetterStatus.ARCHIVED, LetterStatus.IN_REVIEW),
        (LetterStatus.ARCHIVED, LetterStatus.DELIVERED),
        (LetterStatus.RESTORED, LetterStatus.IN_REVIEW),
        (LetterStatus.RESTORED, LetterStatus.APPROVED),
        (LetterStatus.RESTORED, LetterStatus.REJECTED),
        (LetterStatus.RESTORED, LetterStatus.DELIVERED),
        (LetterStatus.RESTORED, LetterStatus.DELETED),
        (LetterStatus.DELETED, LetterStatus.DRAFT),
        (LetterStatus.DELETED, LetterStatus.IN_REVIEW),
        (LetterStatus.DELETED, LetterStatus.APPROVED),
        (LetterStatus.DELETED, LetterStatus.REJECTED),
        (LetterStatus.DELETED, LetterStatus.DELIVERED),
        (LetterStatus.DELETED, LetterStatus.ARCHIVED),
        (LetterStatus.DELETED, LetterStatus.RESTORED),
    ])
    def test_transition_is_not_allowed(self, from_status: LetterStatus, to_status: LetterStatus) -> None:
        allowed = _ALLOWED_WORKFLOW_MATRIX.get(from_status, set())
        assert to_status not in allowed
