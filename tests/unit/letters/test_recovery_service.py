from __future__ import annotations

import pytest

from app.application.letters.recovery_service import RecoveryService, RecoveryServiceError
from app.application.letters.letter_service import LetterService
from app.application.letters.approval_service import ApprovalService
from app.domain.letters.letter import LetterType
from app.domain.letters.letter_status import LetterStatus
from app.domain.letters.archive_state import ArchiveState
from tests.unit.letters.test_services_common import (
    InMemoryAuditRepo,
    InMemoryLetterRepo,
    InMemoryUoW,
)


@pytest.fixture
def letter_repo() -> InMemoryLetterRepo:
    return InMemoryLetterRepo()


@pytest.fixture
def audit_repo() -> InMemoryAuditRepo:
    return InMemoryAuditRepo()


@pytest.fixture
def service(letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> RecoveryService:
    return RecoveryService(letter_repo, audit_repo, lambda: InMemoryUoW())


def make_draft_letter(letter_repo: InMemoryLetterRepo) -> str:
    ls = LetterService(letter_repo, InMemoryAuditRepo(), lambda: InMemoryUoW())
    letter = ls.create_draft(
        letter_type=LetterType.OUTGOING.value,
        subject="Recovery Test",
        body="Body",
        sender_id="user-1",
        sender_name="User",
        sender_department="Dept",
        department_id="dept-1",
        created_by_id="user-1",
    )
    return letter.id


def make_approved_letter(letter_repo: InMemoryLetterRepo) -> str:
    ls = LetterService(letter_repo, InMemoryAuditRepo(), lambda: InMemoryUoW())
    letter = ls.create_draft(
        letter_type=LetterType.OUTGOING.value,
        subject="Approve for Recovery",
        body="Body",
        sender_id="user-1",
        sender_name="User",
        sender_department="Dept",
        department_id="dept-1",
        created_by_id="user-1",
    )
    ls.submit_for_review(letter.id, "user-1")
    approval = ApprovalService(letter_repo, InMemoryAuditRepo(), lambda: InMemoryUoW())
    approval.assign_reviewer(letter.id, "reviewer-1", "Reviewer 1", "Reviewer", "user-1")
    approval.start_review(letter.id, "reviewer-1")
    approval.approve(letter.id, "reviewer-1", "reviewer-1")
    return letter.id


class TestRecoverFailedTransition:
    def test_recover_to_pending_review(self, service: RecoveryService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_draft_letter(letter_repo)
        recovered = service.recover_failed_transition(letter_id, "admin", LetterStatus.PENDING_REVIEW)
        assert recovered.status == LetterStatus.PENDING_REVIEW

    def test_recover_to_approved(self, service: RecoveryService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_draft_letter(letter_repo)
        letter = letter_repo.get_by_id(letter_id)
        letter.status = LetterStatus.IN_REVIEW
        letter_repo.save(letter)
        recovered = service.recover_failed_transition(letter_id, "admin", LetterStatus.APPROVED)
        assert recovered.status == LetterStatus.APPROVED

    def test_recover_invalid_transition(self, service: RecoveryService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_draft_letter(letter_repo)
        with pytest.raises(RecoveryServiceError):
            service.recover_failed_transition(letter_id, "admin", LetterStatus.DELIVERED)

    def test_recover_not_found(self, service: RecoveryService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.recover_failed_transition("nonexistent", "admin", LetterStatus.DRAFT)


class TestRetryOperation:
    def test_retry_submit(self, service: RecoveryService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_draft_letter(letter_repo)
        updated = service.retry_operation(letter_id, "submit", "user-1")
        assert updated.status == LetterStatus.PENDING_REVIEW

    def test_retry_approve(self, service: RecoveryService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_draft_letter(letter_repo)
        letter = letter_repo.get_by_id(letter_id)
        letter.status = LetterStatus.IN_REVIEW
        letter_repo.save(letter)
        updated = service.retry_operation(
            letter_id, "approve", "reviewer-1",
            reviewer_id="reviewer-1", notes="Retried",
        )
        assert updated.status == LetterStatus.APPROVED

    def test_retry_archive(self, service: RecoveryService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_approved_letter(letter_repo)
        updated = service.retry_operation(
            letter_id, "archive", "admin",
            reason="Retry archiving",
        )
        assert updated.status == LetterStatus.ARCHIVED

    def test_retry_unknown_operation(self, service: RecoveryService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_draft_letter(letter_repo)
        with pytest.raises(RecoveryServiceError, match="Unknown retry operation"):
            service.retry_operation(letter_id, "unknown", "admin")


class TestValidateConsistency:
    def test_consistent_letter(self, service: RecoveryService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_draft_letter(letter_repo)
        issues = service.validate_consistency(letter_id)
        assert issues == []

    def test_inconsistent_archived_flag(self, service: RecoveryService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_draft_letter(letter_repo)
        letter = letter_repo.get_by_id(letter_id)
        letter.is_archived = True
        letter_repo.save(letter)
        issues = service.validate_consistency(letter_id)
        assert len(issues) >= 1

    def test_not_found(self, service: RecoveryService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.validate_consistency("nonexistent")


class TestResolveConflict:
    def test_resolve_conflict(self, service: RecoveryService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_draft_letter(letter_repo)
        letter = letter_repo.get_by_id(letter_id)
        letter.is_archived = True
        letter_repo.save(letter)
        resolved = service.resolve_conflict(
            letter_id, "admin",
            LetterStatus.DRAFT, ArchiveState.ACTIVE,
        )
        assert resolved.status == LetterStatus.DRAFT
        assert resolved.archive_state == ArchiveState.ACTIVE
        assert not resolved.is_archived

    def test_resolve_no_conflict(self, service: RecoveryService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_draft_letter(letter_repo)
        with pytest.raises(RecoveryServiceError, match="no consistency issues"):
            service.resolve_conflict(
                letter_id, "admin",
                LetterStatus.DRAFT, ArchiveState.ACTIVE,
            )
