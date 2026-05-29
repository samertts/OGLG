from __future__ import annotations

import pytest

from app.application.letters.approval_result import ApprovalResult
from app.application.letters.approval_service import (
    ApprovalOwnershipError,
    ApprovalService,
)
from app.domain.letters.letter import LetterType
from app.domain.letters.letter_status import LetterStatus
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
def service(letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> ApprovalService:
    return ApprovalService(letter_repo, audit_repo, lambda: InMemoryUoW())


def make_draft(letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo | None = None) -> str:
    from app.application.letters.letter_service import LetterService
    ar = audit_repo or InMemoryAuditRepo()
    ls = LetterService(letter_repo, ar, lambda: InMemoryUoW())
    letter = ls.create_draft(
        letter_type=LetterType.OUTGOING.value,
        subject="Approval Test",
        body="Body",
        sender_id="user-1", sender_name="User", sender_department="Dept",
        department_id="dept-1", created_by_id="user-1",
    )
    letter.pop_events()
    return letter.id


def make_pending_review(letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> str:
    from app.application.letters.letter_service import LetterService
    ls = LetterService(letter_repo, audit_repo, lambda: InMemoryUoW())
    letter = ls.create_draft(
        letter_type=LetterType.OUTGOING.value,
        subject="Approval Test", body="Body",
        sender_id="user-1", sender_name="User", sender_department="Dept",
        department_id="dept-1", created_by_id="user-1",
    )
    ls.submit_for_review(letter.id, "user-1")
    return letter.id


class TestStartReview:
    def test_start_review_success(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        result = service.start_review(letter_id, "reviewer-1")
        assert result.is_ok
        assert result.action == "START_REVIEW"
        assert result.status == LetterStatus.IN_REVIEW

    def test_start_review_idempotent(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.start_review(letter_id, "reviewer-1")
        result = service.start_review(letter_id, "reviewer-1")
        assert result.is_ok
        assert result.action in ("START_REVIEW", "IDEMPOTENT")

    def test_start_review_not_found(self, service: ApprovalService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.start_review("nonexistent", "u1")

    def test_start_review_wrong_status(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_draft(letter_repo, audit_repo)
        result = service.start_review(letter_id, "u1")
        assert result.is_error
        assert result.error_code == "INVALID_STATUS"

    def test_start_review_success_path(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        result = service.start_review(letter_id, "reviewer-1")
        assert result.is_ok
        assert result.action == "START_REVIEW"
        assert result.status == LetterStatus.IN_REVIEW


class TestApprove:
    def test_approve_success(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.start_review(letter_id, "reviewer-1")
        service.assign_reviewer(letter_id, "reviewer-1", "Reviewer One", "Manager", "user-1")
        result = service.approve(letter_id, "reviewer-1", "reviewer-1", "Approved")
        assert result.is_ok
        assert result.action == "APPROVE"
        assert result.status == LetterStatus.APPROVED
        assert result.reviewer_id == "reviewer-1"

    def test_approve_idempotent(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.start_review(letter_id, "reviewer-1")
        service.assign_reviewer(letter_id, "reviewer-1", "R1", "Mgr", "user-1")
        service.approve(letter_id, "reviewer-1", "reviewer-1")
        result = service.approve(letter_id, "reviewer-1", "reviewer-1")
        assert result.is_ok
        assert result.action in ("APPROVE", "IDEMPOTENT") or result.is_idempotent

    def test_approve_not_found(self, service: ApprovalService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.approve("nonexistent", "u1", "u1")

    def test_approve_ownership_violation(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.start_review(letter_id, "reviewer-1")
        service.assign_reviewer(letter_id, "reviewer-1", "R1", "Mgr", "u1")
        with pytest.raises(ApprovalOwnershipError):
            service.approve(letter_id, "wrong-user", "wrong-user")

    def test_approve_generates_events(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.start_review(letter_id, "reviewer-1")
        service.assign_reviewer(letter_id, "reviewer-1", "R1", "Mgr", "u1")
        result = service.approve(letter_id, "reviewer-1", "reviewer-1")
        assert result.is_ok
        assert len(result.events) >= 1

    def test_approve_result_serialization(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.start_review(letter_id, "reviewer-1")
        service.assign_reviewer(letter_id, "reviewer-1", "R1", "Mgr", "u1")
        result = service.approve(letter_id, "reviewer-1", "reviewer-1")
        d = result.to_dict()
        assert d["success"] is True
        assert d["action"] == "APPROVE"
        assert d["status"] == "APPROVED"
        assert d["reviewer_id"] == "reviewer-1"
        assert d["event_count"] >= 1


class TestReject:
    def test_reject_success(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.start_review(letter_id, "reviewer-1")
        service.assign_reviewer(letter_id, "reviewer-1", "R1", "Mgr", "u1")
        result = service.reject(letter_id, "reviewer-1", "reviewer-1", "Missing document")
        assert result.is_ok
        assert result.action == "REJECT"
        assert result.status == LetterStatus.REJECTED

    def test_reject_idempotent(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.start_review(letter_id, "reviewer-1")
        service.assign_reviewer(letter_id, "reviewer-1", "R1", "Mgr", "u1")
        service.reject(letter_id, "reviewer-1", "reviewer-1", "Fix it")
        result = service.reject(letter_id, "reviewer-1", "reviewer-1", "Fix it")
        assert result.is_ok
        assert result.action in ("REJECT", "IDEMPOTENT") or result.is_idempotent

    def test_reject_not_found(self, service: ApprovalService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.reject("nonexistent", "u1", "u1", "reason")

    def test_reject_ownership_violation(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.start_review(letter_id, "reviewer-1")
        service.assign_reviewer(letter_id, "reviewer-1", "R1", "Mgr", "u1")
        with pytest.raises(ApprovalOwnershipError):
            service.reject(letter_id, "wrong-user", "wrong-user", "Nope")


class TestReturnToDraft:
    def test_return_to_draft_success(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.start_review(letter_id, "reviewer-1")
        service.assign_reviewer(letter_id, "reviewer-1", "R1", "Mgr", "u1")
        service.reject(letter_id, "reviewer-1", "reviewer-1", "Fix")
        result = service.return_to_draft(letter_id, "user-1")
        assert result.is_ok
        assert result.action == "RETURN_TO_DRAFT"
        assert result.status == LetterStatus.DRAFT

    def test_return_to_draft_idempotent(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.start_review(letter_id, "reviewer-1")
        service.assign_reviewer(letter_id, "reviewer-1", "R1", "Mgr", "u1")
        service.reject(letter_id, "reviewer-1", "reviewer-1", "Fix")
        service.return_to_draft(letter_id, "user-1")
        result = service.return_to_draft(letter_id, "user-1")
        assert result.is_ok
        assert result.action in ("RETURN_TO_DRAFT", "IDEMPOTENT") or result.is_idempotent

    def test_return_to_draft_not_found(self, service: ApprovalService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.return_to_draft("nonexistent", "u1")

    def test_return_to_draft_invalid_status(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_draft(letter_repo, audit_repo)
        result = service.return_to_draft(letter_id, "u1")
        assert result.is_ok  # Already DRAFT = idempotent


class TestAssignReviewer:
    def test_assign_reviewer_success(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        result = service.assign_reviewer(letter_id, "reviewer-1", "Reviewer One", "Manager", "user-1")
        assert result.is_ok
        assert result.action == "ASSIGN_REVIEWER"

    def test_assign_reviewer_idempotent(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.assign_reviewer(letter_id, "reviewer-1", "R1", "Mgr", "u1")
        result = service.assign_reviewer(letter_id, "reviewer-1", "R1", "Mgr", "u1")
        assert result.is_ok

    def test_assign_reviewer_not_found(self, service: ApprovalService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.assign_reviewer("nonexistent", "r1", "R1", "Mgr", "u1")

    def test_assign_reviewer_not_reviewable(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_draft(letter_repo, audit_repo)
        result = service.assign_reviewer(letter_id, "r1", "R1", "Mgr", "u1")
        assert result.is_error
        assert result.error_code == "NOT_REVIEWABLE"


class TestPendingReviews:
    def test_get_pending_reviews(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        make_pending_review(letter_repo, audit_repo)
        pending = service.get_pending_reviews("reviewer-1")
        assert len(pending) >= 1

    def test_get_in_review(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.start_review(letter_id, "reviewer-1")
        in_review = service.get_in_review("reviewer-1")
        assert len(in_review) >= 1


class TestApprovalResult:
    def test_ok_constructor(self) -> None:
        result = ApprovalResult.ok("l-1", "APPROVE", LetterStatus.APPROVED, "r-1")
        assert result.is_ok
        assert result.action == "APPROVE"
        assert result.reviewer_id == "r-1"

    def test_fail_constructor(self) -> None:
        result = ApprovalResult.fail("l-1", "APPROVE", "Not allowed", "INVALID_STATUS")
        assert result.is_error
        assert result.error_code == "INVALID_STATUS"

    def test_idempotent_constructor(self) -> None:
        result = ApprovalResult.idempotent("l-1", "APPROVE", LetterStatus.APPROVED)
        assert result.is_idempotent

    def test_to_dict_failure(self) -> None:
        result = ApprovalResult.fail("l-1", "REJECT", "No reason", "MISSING_REASON")
        d = result.to_dict()
        assert d["success"] is False
        assert d["error_code"] == "MISSING_REASON"


class TestApprovalOwnership:
    def test_approve_with_unassigned_reviewer_fails(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.start_review(letter_id, "reviewer-1")
        with pytest.raises(ApprovalOwnershipError):
            service.approve(letter_id, "reviewer-1", "reviewer-1")

    def test_assign_multiple_reviewers(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        r1 = service.assign_reviewer(letter_id, "r1", "R1", "Mgr", "u1")
        assert r1.is_ok
        r2 = service.assign_reviewer(letter_id, "r2", "R2", "Dir", "u1")
        assert r2.is_ok
        letter = letter_repo.get_by_id(letter_id)
        assert letter is not None
        active = [r for r in letter.reviews if r.is_current]
        assert len(active) == 1

    def test_current_reviewer_is_last_assigned(self, service: ApprovalService, letter_repo: InMemoryLetterRepo, audit_repo: InMemoryAuditRepo) -> None:
        letter_id = make_pending_review(letter_repo, audit_repo)
        service.assign_reviewer(letter_id, "r1", "R1", "Mgr", "u1")
        service.assign_reviewer(letter_id, "r2", "R2", "Dir", "u1")
        letter = letter_repo.get_by_id(letter_id)
        assert letter is not None
        assert letter.current_reviewer is not None
        assert letter.current_reviewer.reviewer_id == "r2"
