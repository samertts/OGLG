from __future__ import annotations

import pytest

from app.application.letters.approval_service import ApprovalService
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


def make_submitted_letter(
    letter_repo: InMemoryLetterRepo,
    service: ApprovalService,
) -> str:
    from app.application.letters.letter_service import LetterService
    ls = LetterService(letter_repo, audit_repo := InMemoryAuditRepo(), lambda: InMemoryUoW())
    letter = ls.create_draft(
        letter_type=LetterType.OUTGOING.value,
        subject="Approval Test",
        body="Body",
        sender_id="user-1",
        sender_name="User",
        sender_department="Dept",
        department_id="dept-1",
        created_by_id="user-1",
    )
    service._letter_repo = letter_repo
    service._audit_repo = audit_repo
    ls.submit_for_review(letter.id, "user-1")
    return letter.id


class TestStartReview:
    def test_start_review(self, service: ApprovalService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_submitted_letter(letter_repo, service)
        updated = service.start_review(letter_id, "reviewer-1")
        assert updated.status == LetterStatus.IN_REVIEW

    def test_start_review_not_found(self, service: ApprovalService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.start_review("nonexistent", "u1")


class TestApprove:
    def test_approve(self, service: ApprovalService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_submitted_letter(letter_repo, service)
        service.start_review(letter_id, "reviewer-1")
        updated = service.approve(letter_id, "reviewer-1", "reviewer-1", "Approved")
        assert updated.status == LetterStatus.APPROVED

    def test_approve_not_found(self, service: ApprovalService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.approve("nonexistent", "u1", "u1")


class TestReject:
    def test_reject(self, service: ApprovalService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_submitted_letter(letter_repo, service)
        service.start_review(letter_id, "reviewer-1")
        updated = service.reject(letter_id, "reviewer-1", "reviewer-1", "Missing document")
        assert updated.status == LetterStatus.REJECTED

    def test_reject_not_found(self, service: ApprovalService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.reject("nonexistent", "u1", "u1", "reason")


class TestReturnToDraft:
    def test_return_to_draft(self, service: ApprovalService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_submitted_letter(letter_repo, service)
        service.start_review(letter_id, "reviewer-1")
        service.reject(letter_id, "reviewer-1", "reviewer-1", "Fix content")
        updated = service.return_to_draft(letter_id, "reviewer-1")
        assert updated.status == LetterStatus.DRAFT

    def test_return_to_draft_not_found(self, service: ApprovalService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.return_to_draft("nonexistent", "u1")


class TestAssignReviewer:
    def test_assign_reviewer(self, service: ApprovalService, letter_repo: InMemoryLetterRepo) -> None:
        from app.application.letters.letter_service import LetterService
        ls = LetterService(letter_repo, InMemoryAuditRepo(), lambda: InMemoryUoW())
        letter = ls.create_draft(
            letter_type=LetterType.OUTGOING.value,
            subject="Assign Test",
            body="Body",
            sender_id="u1", sender_name="U1", sender_department="D1",
            department_id="d1", created_by_id="u1",
        )
        updated = service.assign_reviewer(letter.id, "reviewer-1", "Reviewer One", "Manager", "u1")
        assert updated.current_reviewer is not None
        assert updated.current_reviewer.reviewer_id == "reviewer-1"

    def test_assign_reviewer_not_found(self, service: ApprovalService) -> None:
        from app.application.letters.letter_service import LetterNotFoundError
        with pytest.raises(LetterNotFoundError):
            service.assign_reviewer("nonexistent", "r1", "R1", "Mgr", "u1")


class TestPendingReviews:
    def test_get_pending_reviews(self, service: ApprovalService, letter_repo: InMemoryLetterRepo) -> None:
        make_submitted_letter(letter_repo, service)
        pending = service.get_pending_reviews("reviewer-1")
        assert len(pending) >= 1

    def test_get_in_review(self, service: ApprovalService, letter_repo: InMemoryLetterRepo) -> None:
        letter_id = make_submitted_letter(letter_repo, service)
        service.start_review(letter_id, "reviewer-1")
        in_review = service.get_in_review("reviewer-1")
        assert len(in_review) >= 1
